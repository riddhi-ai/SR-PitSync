/* dateTime.js: clock synced to the SERVER (India time), so a wrong phone clock cannot break anything */
let OFFSET=0,TZ='Asia/Kolkata';
function syncClock(w){OFFSET=new Date(w.server_time).getTime()-Date.now();TZ=w.timezone||TZ}
const srv=()=>new Date(Date.now()+OFFSET);
function parts(){const o={};new Intl.DateTimeFormat('en-GB',{timeZone:TZ,hourCycle:'h23',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}).formatToParts(srv()).forEach(x=>o[x.type]=x.value);return o}
const todayStr=()=>{const o=parts();return o.year+'-'+o.month+'-'+o.day};
const secOfDay=()=>{const o=parts();return +o.hour*3600+ +o.minute*60+ +o.second};
const toSec=t=>{const p=t.split(':');return p[0]*3600+p[1]*60};
const hm=s=>{const m=Math.max(0,Math.round(s/60));return Math.floor(m/60)+'h '+m%60+'m'};
function cdText(){const n=secOfDay(),s=toSec(S.w.start),e=toSec(S.w.end),p=Math.min(100,Math.max(0,(n-s)/(e-s)*100));
 return (n<s?'Workshop opens in <b>'+hm(s-n)+'</b>':n<e?'Workshop is live. Closes in <b>'+hm(e-n)+'</b>':'Workshop is closed for today')+bar(p)}
