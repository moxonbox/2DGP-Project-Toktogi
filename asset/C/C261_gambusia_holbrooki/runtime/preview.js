'use strict';
const ids=['sex','sequence','action','phase','view','pass','scale','fps','play','seek','markers','canvas','status'];
const ui=Object.fromEntries(ids.map(id=>[id,document.getElementById(id)]));
for(const value of REVIEW.actions)ui.action.add(new Option(value,value));
for(const value of REVIEW.passes)ui.pass.add(new Option(value,value));
ui.action.value='hover_or_school';
const ctx=ui.canvas.getContext('2d'),cache=new Map();let playing=true,time=0,last=0,drawAt=0,generation=0;
function image(path){if(cache.has(path)){const p=cache.get(path);cache.delete(path);cache.set(path,p);return p;}const p=new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(new Error('파일을 열 수 없음: '+path));im.src=path;});cache.set(path,p);while(cache.size>6)cache.delete(cache.keys().next().value);return p;}
function selection(){if(ui.sequence.value!=='clip'){const trace=REVIEW.traces[ui.sex.value+'/'+ui.sequence.value];return {trace,duration:trace.duration,count:trace.frames.length};}const clip=REVIEW.clips[ui.sex.value+'/'+ui.action.value+'/'+ui.phase.value],info=clip.views[ui.view.value];return {clip,info,duration:clip.duration,count:info.samples.length};}
function indexAt(t,duration,count){return Math.min(count-1,Math.max(0,Math.floor(t/duration*count)));}
async function draw(){const gen=++generation;const s=selection(),index=indexAt(time,s.duration,s.count),scale=Number(ui.scale.value);ui.seek.value=time/s.duration;ui.canvas.style.width=(960*scale)+'px';ui.canvas.style.maxWidth='none';ctx.imageSmoothingEnabled=false;
try{if(s.trace){const f=s.trace.frames[index],im=await image(f.frame);if(gen!==generation)return;ctx.clearRect(0,0,960,760);ctx.drawImage(im,0,0);ui.status.textContent=`${f.time.toFixed(2)}s · ${f.action}.${f.phase} · ${f.mode}\n효과 기록 ${f.effects}회 / 재생 위치 이동 시 추가 실행 없음`;return;}
const cell=s.info.samples[index],path=s.info.pass_files[ui.pass.value],im=await image(path),base=ui.pass.value==='sprite'||ui.pass.value==='base'?null:await image(s.info.pass_files.base);if(gen!==generation)return;
ctx.fillStyle='#3d5057';ctx.fillRect(0,0,960,760);const [x,y,w,h]=cell.rect;const offscreen=document.createElement('canvas');offscreen.width=w;offscreen.height=h;const oc=offscreen.getContext('2d');oc.imageSmoothingEnabled=false;oc.drawImage(im,x,y,w,h,0,0,w,h);if(base){oc.globalCompositeOperation='destination-in';oc.drawImage(base,x,y,w,h,0,0,w,h);}const ox=Math.round((960-w)/2),oy=Math.round((760-h)/2);ctx.drawImage(offscreen,ox,oy);
if(ui.markers.checked){for(const [name,marker] of Object.entries(cell.markers)){const [mx,my]=marker.xy;ctx.fillStyle=name==='mouth_tip'?'#ffe18d':'#82d9dc';ctx.fillRect(Math.round(ox+mx)-2,Math.round(oy+my)-2,5,5);ctx.font='12px monospace';ctx.fillText(name,ox+mx+6,oy+my-5);}}
ui.status.textContent=`${ui.sex.value} · ${ui.action.value}.${ui.phase.value} · ${ui.view.value} · ${ui.pass.value}\n${index+1}/${s.count} · ${time.toFixed(3)} / ${s.duration.toFixed(3)}s · ${w}×${h}px`;
}catch(error){ui.status.textContent=error.message;playing=false;ui.play.textContent='재생';}}
for(const id of ['sex','sequence','action','phase','view','pass'])ui[id].onchange=()=>{time=0;draw();};
for(const id of ['scale','markers'])ui[id].onchange=draw;
ui.play.onclick=()=>{playing=!playing;ui.play.textContent=playing?'일시정지':'재생';};
ui.seek.oninput=()=>{time=Number(ui.seek.value)*selection().duration;draw();};
function move(delta){playing=false;ui.play.textContent='재생';const s=selection();time=Math.max(0,Math.min(s.duration-1e-7,(indexAt(time,s.duration,s.count)+delta)*s.duration/s.count));draw();}
document.getElementById('previous').onclick=()=>move(-1);document.getElementById('next').onclick=()=>move(1);
function tick(stamp){if(last&&playing)time=(time+Math.min(.1,(stamp-last)/1000))%selection().duration;last=stamp;if(stamp-drawAt>=1000/Number(ui.fps.value)){drawAt=stamp;draw();}requestAnimationFrame(tick);}
draw();requestAnimationFrame(tick);
