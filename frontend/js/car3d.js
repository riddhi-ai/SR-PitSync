/* car3d.js: interactive 3D Formula Student car (Three.js) */
let scene,cam,ren,car,started=false,GR,GRID,drag=false,PARTS,hov=null,SEL=null,ACT={},fr=0,RAY;
const SUBS=[['chassis','Chassis'],['steering','Steering'],['suspension','Suspension'],['brakes','Brakes'],['lv','LV'],['hv','HV'],['drivetrain','Drivetrain'],['aero','Aerodynamics']];
const nm=k=>SUBS.find(x=>x[0]===k)[1];
const subMembers=k=>roster().filter(m=>m.subsystems.includes(k));
const activeTasks=k=>{const ids=subMembers(k).map(m=>m.id);return S.tasks.filter(t=>t.status!=='done'&&ids.includes(t.assigned_to))};
function refreshActive(){SUBS.forEach(x=>ACT[x[0]]=activeTasks(x[0]).length>0)}
function tip(k){const t=$('#tg');if(!t)return;if(!t.dataset.d)t.dataset.d=t.textContent;t.textContent=k?nm(k)+' · '+subMembers(k).length+' members · '+activeTasks(k).length+' active tasks':t.dataset.d}
function init3D(){const box=$('#hero');if(!box||typeof THREE==='undefined')return;
 scene=new THREE.Scene();cam=new THREE.PerspectiveCamera(40,box.clientWidth/240,.1,100);cam.position.set(5.5,2.8,6.5);cam.lookAt(0,.3,0);
 ren=new THREE.WebGLRenderer({antialias:true,alpha:true});ren.setSize(box.clientWidth,240);ren.setPixelRatio(Math.min(devicePixelRatio,2));box.prepend(ren.domElement);
 scene.add(new THREE.AmbientLight(0xffffff,.6));const l=new THREE.PointLight(0xffffff,1.2);l.position.set(5,8,5);scene.add(l);
 PARTS={};car=new THREE.Group();
 const B=(w,h,d)=>new THREE.BoxGeometry(w,h,d),C=(r,h)=>new THREE.CylinderGeometry(r,r,h,20);
 const add=(sub,g,col,x,y,z,rx)=>{const o=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:col,emissive:col,emissiveIntensity:0,metalness:.5,roughness:.45}));o.position.set(x-.4,y,z);if(rx)o.rotation.x=rx;o.userData={sub,col};car.add(o);if(sub)(PARTS[sub]=PARTS[sub]||[]).push(o)};
 add('chassis',B(2.4,.35,.7),0x22e622,0,.35,0);add('chassis',B(1.2,.25,.3),0x22e622,1.7,.25,0);
 add(0,new THREE.SphereGeometry(.2,16,12),0xf0f0f0,.3,.72,0);
 add('steering',B(.05,.3,.3),0x444444,.7,.72,0);add('steering',B(.5,.06,.06),0x444444,.9,.55,0);
 add('lv',B(.3,.18,.25),0xffc733,-.15,.62,.3);add('hv',B(.8,.35,.5),0xff7a3a,-.75,.7,0);
 add('drivetrain',C(.2,.5),0x6688aa,-1.3,.4,0,Math.PI/2);add('drivetrain',C(.07,1.9),0x6688aa,-1,.38,0,Math.PI/2);
 add('aero',B(.4,.05,1.9),0xf0f0f0,2.3,.12,0);add('aero',B(.4,.05,1.4),0xf0f0f0,-1.5,.95,0);add('aero',B(.05,.6,.05),0xf0f0f0,-1.4,.65,0);
 [1,-1].forEach(z=>{add('aero',B(.4,.3,.04),0xf0f0f0,2.3,.2,z*.95);add('aero',B(.4,.4,.04),0xf0f0f0,-1.5,.95,z*.7)});
 [[1.3,.9],[1.3,-.9],[-1,.95],[-1,-.95]].forEach(p=>{const z=p[1],g=Math.sign(z);add(0,C(.38,.3),0x151515,p[0],.38,z,Math.PI/2);add('brakes',C(.28,.06),0xd03030,p[0],.38,z+g*.18,Math.PI/2);add('suspension',B(.08,.05,.4),0xb8b8b8,p[0],.5,g*.55);add('suspension',B(.08,.05,.4),0xb8b8b8,p[0],.26,g*.55)});
 car.position.y=.1;scene.add(car);GRID=null;paint3D();drag3D(ren.domElement);refreshActive();
 if(!started){started=true;(function loop(){requestAnimationFrame(loop);if(!car||!ren)return;if(!drag&&!hov)car.rotation.y+=.008;fr++;if(fr%30===0)refreshActive();const p=.5+.5*Math.sin(fr/12);for(const k in PARTS)PARTS[k].forEach(o=>{const on=k===hov||k===SEL,a=ACT[k]&&!on;o.material.emissive.set(a?0xffb020:o.userData.col);o.material.emissiveIntensity=on?.9:a?.25+.4*p:0});ren.render(scene,cam)})()}}

function openSub(k){SEL=k;const ms=subMembers(k),ts=activeTasks(k);
 modal(`<div class="row"><h3 style="flex:1">${nm(k)}</h3><button class="cls">Close</button></div><h2>Team (${ms.length})</h2>${ms.map(m=>`<div class="row" style="margin:6px 0">${av(m,m.status)}<div><b>${esc(m.name)}</b><div class="mu">${esc(m.role_text)} · ${label[m.status]}</div></div></div>`).join('')||'<p class="mu">No members on this subsystem yet.</p>'}<h2>Active tasks (${ts.length})</h2>${ts.map(t=>`<div style="margin:6px 0">${esc(t.title)}<div class="mu">${esc(t.assignee_name)} · ${TS[t.status]}</div>${bar(t.progress)}</div>`).join('')||'<p class="mu">No active tasks.</p>'}${S.me.is_coordinator?'<p><button class="pri" id="ga">Assign a task</button></p>':''}`,(o,x)=>{const g=o.querySelector('#ga');if(g)g.onclick=()=>{x();go('tasks')}})}
function chips(){const c=$('#chips');if(!c)return;c.innerHTML=SUBS.map(x=>{const n=activeTasks(x[0]).length;return `<button data-sub="${x[0]}">${x[1]}${n?`<b>${n}</b>`:''}</button>`}).join('')+'<span class="mu" style="white-space:nowrap;align-self:center">Amber glow = active tasks</span>';c.querySelectorAll('[data-sub]').forEach(b=>{b.onclick=()=>openSub(b.dataset.sub);b.onmouseenter=()=>hov=b.dataset.sub;b.onmouseleave=()=>hov=null})}
function paint3D(){if(!PARTS||!scene)return;const c=new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--g').trim());(PARTS.chassis||[]).forEach(o=>{o.material.color.copy(c);o.userData.col=c.getHex()});if(GRID)scene.remove(GRID);GRID=new THREE.GridHelper(14,28,c,c.clone().multiplyScalar(.2));GRID.position.y=-.02;scene.add(GRID)}
function drag3D(el){let x=0,x0=0;el.style.touchAction='pan-y';RAY=RAY||new THREE.Raycaster();
 const pick=e=>{const r=el.getBoundingClientRect();RAY.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-((e.clientY-r.top)/r.height)*2+1),cam);const h=RAY.intersectObjects(car.children)[0];return h&&h.object.userData.sub||null};
 el.onpointerdown=e=>{drag=true;x=x0=e.clientX;el.setPointerCapture(e.pointerId)};
 el.onpointermove=e=>{if(drag&&car){car.rotation.y+=(e.clientX-x)*.01;x=e.clientX}else{hov=pick(e);tip(hov);el.style.cursor=hov?'pointer':'grab'}};
 el.onpointerup=e=>{drag=false;if(Math.abs(e.clientX-x0)<6){const k=pick(e);if(k)openSub(k)}};el.onpointercancel=()=>{drag=false};el.onpointerleave=()=>{hov=null;tip(null)}}
function setTheme(t){document.documentElement.setAttribute('data-theme',t);try{localStorage.setItem('pitsync-theme',t)}catch(e){}paint3D()}
addEventListener('resize',()=>{const b=$('#hero');if(ren&&b&&cam){cam.aspect=b.clientWidth/240;cam.updateProjectionMatrix();ren.setSize(b.clientWidth,240)}});
