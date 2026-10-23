const p=require('puppeteer-core'),fs=require('fs');(async()=>{const b=await p.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});const pg=await b.newPage();
for(const f of ['m2w1.html']){await pg.goto('http://localhost:8765/'+f,{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,800));
const r=await pg.evaluate(()=>{const m=[...document.querySelectorAll('pre.mermaid')];return {n:m.length,ok:m.filter(x=>x.querySelector('svg')&&!x.textContent.includes('Syntax error')).length}});if(r.n!==r.ok)console.log(f,r);}
await pg.goto('http://localhost:8765/',{waitUntil:'networkidle0'});await pg.screenshot({path:'/tmp/home.png'});console.log('done');await b.close();})();
