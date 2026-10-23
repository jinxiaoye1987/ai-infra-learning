const fs=require('fs'),path=require('path');const {marked}=require('marked');const hljs=require('highlight.js');
const OUT='dist';fs.rmSync(OUT,{recursive:true,force:true});fs.mkdirSync(OUT+'/assets',{recursive:true});
fs.copyFileSync('node_modules/mermaid/dist/mermaid.min.js',OUT+'/assets/mermaid.min.js');
fs.copyFileSync('static/style.css',OUT+'/assets/style.css');fs.copyFileSync('static/app.js',OUT+'/assets/app.js');
if(fs.existsSync('static/img')){fs.mkdirSync(OUT+'/assets/img',{recursive:true});for(const f of fs.readdirSync('static/img'))fs.copyFileSync('static/img/'+f,OUT+'/assets/img/'+f);}
const files=fs.readdirSync('content').filter(f=>f.endsWith('.md')).sort();
const pages=[];
for(const f of files){const txt=fs.readFileSync('content/'+f,'utf8');
  for(const chunk of txt.split(/^=== /m).filter(s=>s.trim())){const nl=chunk.indexOf('\n');
    const [slug,title,section]=chunk.slice(0,nl).split('|').map(s=>s.trim());pages.push({slug,title,section,md:chunk.slice(nl+1)});}}
const TAGS={local:['tag-local','本地可做'],gpu1:['tag-gpu1','租单卡 GPU（24GB）'],gpuN:['tag-gpun','租多卡 GPU（2–4 卡）'],none:['tag-none','纯阅读 / 纸笔']};
const TAGICON={local:'💻',gpu1:'🟡',gpuN:'🔴',none:'📖'};
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const LANGNAME={bash:'terminal',sh:'terminal',shell:'terminal',python:'python',yaml:'yaml',json:'json',sql:'sql',text:'output',txt:'output','':'text'};
// 给代码块找文件名：fence 前 3 行内的 `xxx.py` 或 docstring 开头的 xxx.py：
function addTitles(md){const L=md.split('\n');let inF=false;
  for(let i=0;i<L.length;i++){const m=L[i].match(/^```(\w*)\s*$/);if(!m)continue;
    if(inF){inF=false;continue}inF=true;const lang=m[1];if(lang==='mermaid'||lang==='text'||lang==='')continue;
    let t=null;const first=(L[i+1]||'');const d=first.match(/^(?:"""|#\s*)([\w./-]+\.(?:py|ya?ml|json|sh|sql))[：:\s]/);if(d)t=d[1];
    for(let j=i-1,k=0;!t&&j>=0&&k<3;j--){if(!L[j].trim())continue;k++;if(/^```|^#/.test(L[j]))break;
      const f=[...L[j].matchAll(/`([\w./-]+\.(?:py|ya?ml|json|sh|sql))`/g)];if(f.length===1)t=f[0][1];}
    if(t)L[i]='```'+lang+' title='+t;}
  return L.join('\n');}
const renderer=new marked.Renderer();
renderer.code=function(code,info){info=(info||'').trim();const lang=info.split(/\s+/)[0]||'';const tm=info.match(/title=(\S+)/);
  if(lang==='mermaid')return `<div class="diagram"><pre class="mermaid">${esc(code)}</pre></div>`;
  let body;try{body=lang&&hljs.getLanguage(lang)&&lang!=='text'?hljs.highlight(code,{language:lang,ignoreIllegals:true}).value:esc(code)}catch(e){body=esc(code)}
  const lines=code.replace(/\n$/,'').split('\n').length;const ln=lines>3&&lang!=='text';
  const label=LANGNAME[lang]||lang;const kind=['bash','sh','shell'].includes(lang)?'term':lang==='text'?'out':'src';
  const nums=ln?`<span class="ln" aria-hidden="true">${Array.from({length:lines},(_,i)=>i+1).join('\n')}</span>`:'';
  return `<figure class="code ${kind}"><figcaption><span class="dots"><i></i><i></i><i></i></span><span class="fname">${tm?esc(tm[1]):''}</span><span class="lang">${esc(label)}</span><button class="copy" type="button" aria-label="复制代码">复制</button></figcaption><pre class="${ln?'has-ln':''}">${nums}<code class="hljs language-${esc(lang)}">${body}</code></pre></figure>`;};
const used={};const slugify=t=>{let s=t.replace(/<[^>]+>/g,'').toLowerCase().trim().replace(/[^\w\u4e00-\u9fff]+/g,'-').replace(/^-|-$/g,'')||'sec';if(used[s]){s+='-'+(++used[s])}else used[s]=1;return s};
let TOC=[];
renderer.heading=function(text,level){const id=slugify(text);if(level===2||level===3)TOC.push({l:level,id,t:text.replace(/<span class="tag[\s\S]*?<\/span>/g,'').replace(/<[^>]+>/g,'').trim()});return `<h${level} id="${id}"><a class="anchor" href="#${id}">#</a>${text}</h${level}>`;};
renderer.table=function(h,b){return `<div class="table-wrap"><table><thead>${h}</thead><tbody>${b}</tbody></table></div>`;};
renderer.blockquote=function(q){const plain=q.replace(/<[^>]+>/g,'');let k='note',icon='ℹ️';
  if(/^\s*本周一句话/.test(plain)){k='hero';icon='🎯'}
  else if(/未(在本站)?实测|需 GPU|验证说明/.test(plain)){k='warn';icon='⚠️'}
  else if(/^\s*(坑|注意|警告)/.test(plain)){k='danger';icon='🚫'}
  else if(/^\s*(经验法则|提示|技巧|提醒|读书版本)/.test(plain)){k='tip';icon='💡'}
  return `<aside class="callout callout-${k}"><span class="ci">${icon}</span><div class="cb">${q}</div></aside>`;};
marked.setOptions({renderer,gfm:true});
const sections=[...new Set(pages.map(p=>p.section))];
const href=s=>'/'+(s==='index'?'':s+'.html');
const nav=cur=>sections.map(s=>{const ps=pages.filter(p=>p.section===s);const open=ps.some(p=>p.slug===cur)||s===sections[0];
  return `<details class="navsec" ${open?'open':''}><summary>${s}</summary>`+ps.map(p=>`<a href="${href(p.slug)}" class="${p.slug===cur?'cur':''}" data-slug="${p.slug}"><span class="dot"></span><span>${p.title}</span></a>`).join('')+'</details>'}).join('');
const index=[],progress={};
pages.forEach((p,i)=>{let n=0;TOC=[];for(const k in used)delete used[k];
  let md=addTitles(p.md).replace(/\{\{(local|gpu1|gpuN|none)\}\}/g,(_,t)=>`<span class="tag ${TAGS[t][0]}">${TAGICON[t]} ${TAGS[t][1]}</span>`);
  let html=marked.parse(md);
  html=html.replace(/<li>\s*\[( |x)\]\s*/g,()=>`<li class="chk"><input type="checkbox" data-id="${p.slug}:${n++}"> `);
  html=html.replace(/<li>\s*<input (checked="" )?disabled="" type="checkbox">\s*/g,()=>`<li class="chk"><input type="checkbox" data-id="${p.slug}:${n++}"> `);
  html=html.replace(/<details>/g,'<details class="qa">');
  progress[p.slug]={title:p.title,total:n,section:p.section};
  const prev=pages[i-1],next=pages[i+1];
  const pn=`<nav class="pn">${prev?`<a class="prev" href="${href(prev.slug)}"><small>上一篇</small><span>← ${prev.title}</span></a>`:'<span></span>'}${next?`<a class="next" href="${href(next.slug)}"><small>下一篇</small><span>${next.title} →</span></a>`:''}</nav>`;
  const toc=TOC.length>=4?`<aside id="toc"><div class="toch">本页目录</div>${TOC.map(t=>`<a class="l${t.l}" href="#${t.id}">${esc(t.t)}</a>`).join('')}</aside>`:'';
  const page=`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${p.title} · AI Infra 转型自学教程</title>
<script>(function(){var t=localStorage.getItem('aiinfra-theme');if(t==='dark'||(!t&&matchMedia('(prefers-color-scheme: dark)').matches))document.documentElement.classList.add('dark')})()</script>
<link rel="stylesheet" href="/assets/style.css"></head>
<body data-slug="${p.slug}" class="${toc?'has-toc':''}"><div id="readbar"></div><header><button id="menu" aria-label="菜单">☰</button><a href="/" class="brand"><span class="logo">AI</span><span>大数据 → AI Infra 架构师</span></a><div class="hsp"></div><div class="search"><input id="q" placeholder="搜索教程…" autocomplete="off"><kbd>/</kbd><div id="qr"></div></div><button id="theme" aria-label="切换主题">◐</button></header>
<nav id="side">${nav(p.slug)}</nav><div class="wrap"><main><div class="crumb"><span>${p.section}</span></div><article class="prose">${html}</article>${pn}</main>${toc}</div>
<script src="/assets/mermaid.min.js"></script><script src="/assets/app.js"></script></body></html>`;
  fs.writeFileSync(path.join(OUT,(p.slug==='index'?'index':p.slug)+'.html'),page);
  index.push({s:p.slug,t:p.title,sec:p.section,x:html.replace(/<span class="ln"[^>]*>[\d\n]*<\/span>/g,'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ')});
});
fs.writeFileSync(OUT+'/assets/search.json',JSON.stringify(index));
fs.writeFileSync(OUT+'/assets/progress.json',JSON.stringify(progress));
fs.writeFileSync(OUT+'/_headers','/*\n  X-Robots-Tag: noindex\n  Cache-Control: no-cache\n');
console.log('pages',pages.length,'checkboxes',Object.values(progress).reduce((a,b)=>a+b.total,0));
