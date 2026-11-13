#!/usr/bin/env node
// 构建后的站内检查：页面数量、周页、未实测标注、站内链接，以及当前树里不该出现的产物。
const fs = require('fs');
const path = require('path');

const siteDir = __dirname;
const dist = path.join(siteDir, 'dist');
const repo = path.resolve(siteDir, '..');
const errors = [];

const expected = [
  'index.html', 'lab-env.html', 'lab-cost.html', 'mapping.html',
  'm1.html', 'm1w1.html', 'm1w2.html', 'm1w3.html', 'm1w4.html',
  'm2.html', 'm2w1.html', 'm2w2.html', 'm2w3.html', 'm2w4.html',
  'm3.html', 'm3w1.html', 'm3w2.html', 'm3w3.html', 'm3w4.html',
  'm4.html', 'm4w1.html', 'm4w2.html', 'm4w3.html', 'm4w4.html',
  'm5.html', 'm5w1.html', 'm5w2.html', 'm5w3.html', 'm5w4.html',
  'm6.html', 'm6w1.html', 'm6w2.html', 'm6w3.html', 'm6w4.html',
  'resources.html', 'jobs.html', 'cases.html', 'advice.html',
];
const mustUntested = [
  'm1w3', 'm1w4', 'm2w4', 'm3w1', 'm3w2', 'm3w3', 'm3w4',
  'm4w2', 'm4w3', 'm4w4', 'm5w2', 'm5w3', 'm6w2',
];

function walk(dir, acc = []) {
  if (!fs.existsSync(dir)) return acc;
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ent.name === '.git' || ent.name === 'node_modules' || ent.name === 'dist') continue;
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p, acc);
    else acc.push(p);
  }
  return acc;
}

if (!fs.existsSync(dist)) {
  errors.push('缺少 site/dist，请先运行 node build.js');
} else {
  const html = new Set(fs.readdirSync(dist).filter((name) => name.endsWith('.html')));
  if (html.size !== expected.length) errors.push(`页面数量 ${html.size}，期望 ${expected.length}`);
  for (const name of expected) {
    if (!html.has(name)) errors.push(`缺少页面 ${name}`);
  }
  for (const name of html) {
    if (!expected.includes(name)) errors.push(`意外页面 ${name}`);
  }
  for (const slug of mustUntested) {
    const file = path.join(dist, `${slug}.html`);
    if (!fs.existsSync(file)) continue;
    const text = fs.readFileSync(file, 'utf8');
    if (!text.includes('未在本站实测')) errors.push(`${slug} 缺少「未在本站实测」标注`);
  }

  const attr = /(?:href|src)="([^"]*)"/g;
  for (const name of html) {
    const file = path.join(dist, name);
    const text = fs.readFileSync(file, 'utf8');
    let match;
    while ((match = attr.exec(text))) {
      const href = match[1];
      if (!href || /^(https?:|mailto:|javascript:|#|\/\/)/.test(href)) continue;
      const raw = href.split('#')[0].split('?')[0];
      if (!raw) continue;
      let abs;
      if (raw.startsWith('/')) abs = raw;
      else {
        const dir = path.posix.dirname(`/${name}`);
        abs = path.posix.normalize(path.posix.join(dir, raw));
      }
      if (abs.endsWith('/')) abs += 'index.html';
      if (abs === '/') abs = '/index.html';
      const local = path.join(dist, abs.replace(/^\//, ''));
      if (!fs.existsSync(local)) errors.push(`${name} -> ${href}`);
    }
  }
}

const bannedExt = new Set(['.safetensors', '.pkl', '.pem', '.pt', '.pth', '.onnx', '.mp4', '.webm', '.mov']);
for (const file of walk(repo)) {
  const parts = file.split(path.sep);
  const base = path.basename(file);
  if (parts.includes('mlruns') || base === '.env' || base === 'mlflow.db' || bannedExt.has(path.extname(file).toLowerCase())) {
    errors.push(`当前树含有不应提交的产物：${path.relative(repo, file)}`);
  }
}

const secretExt = new Set(['.md', '.js', '.json', '.yml', '.yaml', '.txt', '.py', '.sh', '.css', '.html']);
const secretRe = /-----BEGIN [A-Z ]*PRIVATE KEY-----|@gmail\.com/i;
for (const file of walk(repo)) {
  if (!secretExt.has(path.extname(file).toLowerCase())) continue;
  const text = fs.readFileSync(file, 'utf8');
  if (secretRe.test(text)) errors.push(`当前树含有私钥标记或个人邮箱域名：${path.relative(repo, file)}`);
}

if (errors.length) {
  console.error(`check_content 失败，共 ${errors.length} 项`);
  for (const item of errors.slice(0, 40)) console.error(`- ${item}`);
  process.exit(1);
}
console.log(`check_content ok pages=${expected.length} untested=${mustUntested.length}`);
