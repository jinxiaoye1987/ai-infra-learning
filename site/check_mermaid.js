// 用法：node check_mermaid.js m1w2 m1w3 ...（需先在 dist 上起 http 服务于 8765）
const p=require('puppeteer-core');(async()=>{const b=await p.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});const pg=await b.newPage();
for(const s of process.argv.slice(2)){await pg.goto('http://localhost:8765/'+s+'.html',{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,1500));
const r=await pg.evaluate(()=>{const m=[...document.querySelectorAll('pre.mermaid')];return {n:m.length,bad:m.map((x,i)=>[i,x.querySelector('svg')&&!x.textContent.includes('Syntax error')?0:1,x.getAttribute('data-processed')]).filter(z=>z[1]).map(z=>z[0]),chk:document.querySelectorAll('input[type=checkbox]').length,det:document.querySelectorAll('details').length}});console.log(s,JSON.stringify(r));}
await b.close();})();
