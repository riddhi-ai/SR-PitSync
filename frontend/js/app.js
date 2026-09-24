/* app.js: page shell, tab switching, live clock and start-up */
let vseq=0;
function shell(){const co=S.me.is_coordinator;
 const tabs=co?[['pit',"Who's In"],['dash','Dashboard'],['tasks','Tasks'],['team','Team'],['time','Timing'],['mail','Outbox'],['prof','Profile']]:[['pit',"Who's In"],['att','My Attendance'],['tasks','My Tasks'],['prof','Profile']];
 $('#app').innerHTML=`<div class="wrap"><header><img src="assets/images/logo.png" alt="STES Racing"><div class="clock"><span id="clk"></span><small id="dt"></small><button id="out" style="padding:2px 8px;margin-top:3px;font-size:.75rem">Log out</button></div></header>
<div id="hero"><div class="sw">${THEMES.map(t=>`<button aria-label="${t[0]} theme" data-th="${t[0]}" style="--c:${t[1]}"></button>`).join('')}</div><div class="tag" id="tg">SR PITSYNC · ${co?'Coordinator':'Member'}: ${esc(S.me.name)}</div></div>
<div class="row chips" id="chips"></div><nav>${tabs.map(t=>`<button data-t="${t[0]}">${t[1]}</button>`).join('')}</nav><main id="main"></main></div>`;
 $('#out').onclick=()=>logout();
 document.querySelectorAll('[data-th]').forEach(b=>b.onclick=()=>setTheme(b.dataset.th));
 document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>go(b.dataset.t));
 init3D();go(S.tab);tick()}
function go(t){S.tab=t;document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));view()}
async function view(quiet){const id=++vseq,v=VIEWS[S.tab];if(!v||!$('#main'))return;
 if(!quiet)$('#main').innerHTML='<div class="load" style="height:25vh"><div class="spin"></div></div>';
 try{if(v.load)await v.load()}catch(e){toast(e.message,true)}
 if(id!==vseq||!$('#main'))return;
 try{$('#main').innerHTML=v.html();if(v.bind)v.bind();chips()}catch(e){$('#main').innerHTML='<p class="err">Could not show this page.</p>'}}
function tick(){const c=$('#clk');if(c){const d=srv();c.textContent=d.toLocaleTimeString('en-GB',{timeZone:TZ});$('#dt').textContent=d.toLocaleDateString('en-IN',{timeZone:TZ,weekday:'long',day:'numeric',month:'short',year:'numeric'})}
 const cd=$('#cd');if(cd)cd.innerHTML=cdText();
 if(S.me&&S.day&&todayStr()!==S.day){S.day=todayStr();view()}}
setInterval(tick,1000);
setInterval(async()=>{if(!S.me||document.hidden||!['pit','dash'].includes(S.tab)||document.querySelector('.modal')||document.activeElement.id==='sq')return;try{await Promise.all([loadWho(),loadTasks()]);view(true)}catch(e){}},30000);
async function enter(){await loadW();await Promise.all([loadWho(),loadTasks()]);S.day=todayStr();S.tab=S.me.must_change_password?'prof':'pit';shell();if(S.me.must_change_password)toast('Please set a new password')}
async function start(){try{setTheme(localStorage.getItem('pitsync-theme')||'volt')}catch(e){}
 if(!getToken())return loginView();
 try{S.me=await api('/members/me');await enter()}catch(e){loginView()}}
start();
