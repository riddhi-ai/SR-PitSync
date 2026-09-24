/* ui.js: shared state and small helpers */
const S={me:null,who:null,tasks:[],team:[],mail:[],w:{start:'10:00',end:'17:00'},tab:'pit',day:''};
const VIEWS={};
const $=s=>document.querySelector(s);
const THEMES=[['volt','#22e622'],['red','#ff3b3b'],['blue','#3ea6ff'],['amber','#ffb020']];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const colors={present:'var(--ok)',coming:'var(--y)',absent:'var(--r)',not_updated:'var(--mu)'};
const label={present:'Present',coming:'Coming',absent:'Absent',not_updated:'Not updated'};
const TS={todo:'To do',in_progress:'In progress',done:'Done'};
const roster=()=>S.who?S.who.members:[];
const rowOf=id=>roster().find(m=>m.id===id);
const bar=p=>`<div class="bar"><i style="width:${p}%"></i></div>`;
const av=(m,st)=>m.photo_url?`<img class="av" style="--c:${colors[st||'not_updated']}" src="${esc(imgUrl(m.photo_url))}" alt="">`:`<div class="av" style="--c:${colors[st||'not_updated']}">${esc(m.name.slice(0,2).toUpperCase())}</div>`;
function toast(t,bad){const e=document.createElement('div');e.className='toast'+(bad?' err':'');e.textContent=t;document.body.append(e);setTimeout(()=>e.remove(),bad?4000:2600)}
async function run(fn){try{return await fn()}catch(e){toast(e.message,true)}}
function modal(h,cb){const o=document.createElement('div');o.className='modal';o.innerHTML='<div class="card" role="dialog">'+h+'</div>';const x=()=>{SEL=null;o.remove();document.removeEventListener('keydown',k)},k=e=>{if(e.key==='Escape')x()};o.onclick=e=>{if(e.target===o)x()};o.querySelector('.cls').onclick=x;document.addEventListener('keydown',k);document.body.append(o);if(cb)cb(o,x)}
