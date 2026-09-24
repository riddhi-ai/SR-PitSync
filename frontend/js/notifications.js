/* notifications.js: coordinator email outbox (emails themselves are sent by the backend) */
const loadMail=async()=>{S.mail=await api('/notifications/log')};
function mailV(){return `<h2>Email outbox</h2><p class="mu">Every notification the system sends is listed here.</p>${S.mail.map(m=>{const st=m.sent?['Sent','var(--ok)']:m.error.includes('not configured')?['Logged only','var(--y)']:m.error?['Failed','var(--r)']:['Pending','var(--mu)'];return `<div class="mail"><b>${esc(m.subject)}</b> <span class="pill" style="--c:${st[1]}">${st[0]}</span><div class="mu">To: ${esc(m.to)}</div></div>`}).join('')||'<p class="mu">Nothing sent yet.</p>'}`}
VIEWS.mail={html:mailV,load:loadMail};
