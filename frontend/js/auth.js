/* auth.js: login and logout */
function loginView(msg){$('#app').innerHTML=`<div class="wrap login card"><img src="assets/images/logo.png" alt="STES Racing" style="width:100%;background:#000;border-radius:10px"><h1 style="font-size:1.6rem;margin:6px 0">SR PITSYNC</h1><p class="mu">Log in with the email and password your coordinator gave you.</p>
<form id="lf"><label for="em">Email</label><input id="em" type="email" autocomplete="username" required><label for="pw">Password</label><input id="pw" type="password" autocomplete="current-password" required><p class="err" id="le">${esc(msg||'')}</p><button class="pri" style="width:100%">Log in</button></form></div>`;
 $('#lf').onsubmit=async e=>{e.preventDefault();const b=e.target.querySelector('button');b.disabled=true;
  try{const d=await api('/auth/login',{method:'POST',body:{email:$('#em').value.trim(),password:$('#pw').value}});setToken(d.access_token);S.me=d.member;await enter()}
  catch(x){$('#le').textContent=x.message;b.disabled=false}}}
function logout(expired){setToken(null);S.me=null;S.who=null;S.tasks=[];loginView(expired?'Your session expired. Please log in again.':'')}
