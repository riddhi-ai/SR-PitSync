/* api.js: the ONLY file that talks to the backend. Change API_BASE when you deploy. */
const API_BASE='https://sr-pitsync.onrender.com';
const getToken=()=>{try{return localStorage.getItem('pitsync-token')}catch(e){return null}};
const setToken=t=>{try{t?localStorage.setItem('pitsync-token',t):localStorage.removeItem('pitsync-token')}catch(e){}};
const imgUrl=p=>!p?'':p.startsWith('http')?p:API_BASE+p;
async function api(path,{method='GET',body,form}={}){
 const h={},t=getToken();if(t)h.Authorization='Bearer '+t;
 let b;if(form)b=form;else if(body){h['Content-Type']='application/json';b=JSON.stringify(body)}
 let r;try{r=await fetch(API_BASE+path,{method,headers:h,body:b})}catch(e){throw new Error('Cannot reach the server. Is the backend running?')}
 const d=await r.json().catch(()=>({}));
 if(r.status===401&&t&&path!=='/auth/login'){logout(true);throw new Error('Session expired')}
 if(!r.ok){let m=d.detail;if(Array.isArray(m))m=m.map(x=>x.msg).join('; ');throw new Error(m||'Something went wrong')}
 return d}