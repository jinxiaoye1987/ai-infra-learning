const dark=()=>document.documentElement.classList.contains('dark');
const MV=d=>d?{darkMode:true,background:'transparent',primaryColor:'#1e293b',primaryBorderColor:'#3b82f6',primaryTextColor:'#e2e8f0',lineColor:'#64748b',secondaryColor:'#052e16',tertiaryColor:'#172554',clusterBkg:'#0f172a',clusterBorder:'#334155',fontFamily:'system-ui,"PingFang SC","Noto Sans CJK SC",sans-serif'}
 :{background:'transparent',primaryColor:'#eff6ff',primaryBorderColor:'#3b82f6',primaryTextColor:'#1e293b',lineColor:'#64748b',secondaryColor:'#ecfdf5',tertiaryColor:'#f8fafc',clusterBkg:'#f8fafc',clusterBorder:'#cbd5e1',fontFamily:'system-ui,"PingFang SC","Noto Sans CJK SC",sans-serif'};
document.querySelectorAll('pre.mermaid').forEach(e=>e.dataset.src=e.textContent);
function renderMermaid(){mermaid.initialize({startOnLoad:false,theme:'base',themeVariables:MV(dark()),securityLevel:'loose'});
 document.querySelectorAll('pre.mermaid').forEach(e=>{e.removeAttribute('data-processed');e.textContent=e.dataset.src});mermaid.run({querySelector:'pre.mermaid'}).catch(()=>{});}
renderMermaid();
document.getElementById('theme').onclick=()=>{const d=!dark();document.documentElement.classList.toggle('dark',d);localStorage.setItem('aiinfra-theme',d?'dark':'light');renderMermaid();};
document.querySelectorAll('button.copy').forEach(b=>b.onclick=async()=>{const c=b.closest('figure').querySelector('code').innerText;
 try{await navigator.clipboard.writeText(c)}catch(e){const t=document.createElement('textarea');t.value=c;document.body.appendChild(t);t.select();document.execCommand('copy');t.remove()}
 b.textContent='已复制 ✓';b.classList.add('ok');setTimeout(()=>{b.textContent='复制';b.classList.remove('ok')},1500)});
const K='aiinfra-progress',st=JSON.parse(localStorage.getItem(K)||'{}');const save=()=>localStorage.setItem(K,JSON.stringify(st));
document.querySelectorAll('input[data-id]').forEach(c=>{c.checked=!!st[c.dataset.id];c.onchange=()=>{st[c.dataset.id]=c.checked;save();mark();}});
document.getElementById('menu').onclick=()=>document.getElementById('side').classList.toggle('open');
const cur=document.querySelector('nav#side a.cur');if(cur)cur.scrollIntoView({block:'center'});
let P=null;fetch('/assets/progress.json').then(r=>r.json()).then(p=>{P=p;mark();overview();});
function cnt(s){let d=0;for(let i=0;i<P[s].total;i++)if(st[s+':'+i])d++;return d}
function mark(){if(!P)return;document.querySelectorAll('nav a[data-slug]').forEach(a=>{const s=a.dataset.slug;if(P[s]&&P[s].total&&cnt(s)===P[s].total)a.classList.add('done');else a.classList.remove('done')});overview();}
function overview(){const el=document.getElementById('overview');if(!el||!P)return;let T=0,D=0,rows='';const secs={};
for(const s in P){if(!P[s].total)continue;T+=P[s].total;const d=cnt(s);D+=d;(secs[P[s].section]=secs[P[s].section]||[0,0]);secs[P[s].section][0]+=d;secs[P[s].section][1]+=P[s].total;}
for(const k in secs){const[d,t]=secs[k];rows+=`<tr><td>${k}</td><td>${d}/${t}</td><td><div class="bar"><i style="width:${t?d*100/t:0}%"></i></div></td></tr>`}
el.innerHTML=`<p><b>总进度：${D}/${T}（${T?Math.round(D*100/T):0}%）</b> · 勾选状态只存在本浏览器（localStorage）</p><div class="table-wrap"><table class="prog"><thead><tr><th>阶段</th><th>完成</th><th>进度</th></tr></thead><tbody>${rows}</tbody></table></div><button onclick="if(confirm('清空所有勾选？')){localStorage.removeItem(K);location.reload()}">重置进度</button>`;}
let IDX=null;const q=document.getElementById('q'),qr=document.getElementById('qr');
q.oninput=async()=>{const v=q.value.trim().toLowerCase();if(!v){qr.style.display='none';return}
if(!IDX)IDX=await (await fetch('/assets/search.json')).json();
const terms=v.split(/\s+/);const res=IDX.filter(p=>terms.every(t=>(p.t+p.x).toLowerCase().includes(t))).slice(0,20);
qr.innerHTML=res.map(p=>{const i=p.x.toLowerCase().indexOf(terms[0]);const sn=p.x.slice(Math.max(0,i-30),i+60);return `<a href="/${p.s==='index'?'':p.s+'.html'}">${p.t}<small>${p.sec} · …${sn.replace(/</g,'&lt;')}…</small></a>`}).join('')||'<a>无结果</a>';qr.style.display='block';};
document.addEventListener('click',e=>{if(!qr.contains(e.target)&&e.target!==q)qr.style.display='none'});
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus()}if(e.key==='Escape'){qr.style.display='none';q.blur()}});
const rb=document.getElementById('readbar');const tl=[...document.querySelectorAll('#toc a')];const hs=tl.map(a=>document.getElementById(a.getAttribute('href').slice(1)));
addEventListener('scroll',()=>{const h=document.documentElement;rb.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';
 if(tl.length){let k=0;hs.forEach((x,i)=>{if(x&&x.getBoundingClientRect().top<120)k=i});tl.forEach((a,i)=>a.classList.toggle('on',i===k))}},{passive:true});
