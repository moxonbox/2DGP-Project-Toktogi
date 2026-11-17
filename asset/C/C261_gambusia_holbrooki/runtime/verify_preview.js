'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path'),root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'GambusiaMotionPreview.html'),'utf8');
const data=JSON.parse(html.match(/const REVIEW=(.*?);<\/script>/s)[1]);
const assert=require('assert');let requested=[],drawn=[];
const ctx={clearRect(){},fillRect(){},fillText(){},drawImage(im){drawn.push(im.src||'canvas');}};
const defaults={sex:'female',sequence:'clip',action:'hover_or_school',phase:'mid',view:'left',pass:'sprite',scale:'1',fps:'20',seek:'0'};
const nodes={};for(const id of ['sex','sequence','action','phase','view','pass','scale','fps','play','seek','markers','canvas','status','previous','next'])nodes[id]={value:defaults[id]||'',style:{},add(){},getContext(){return ctx;}};
class FakeImage{set src(value){assert(fs.existsSync(path.join(root,value)),value);this._src=value;requested.push(value);queueMicrotask(()=>this.onload());}get src(){return this._src;}}
const sandbox={REVIEW:data,document:{getElementById:id=>nodes[id],createElement:()=>({getContext:()=>ctx})},Option:class{},Image:FakeImage,requestAnimationFrame(){},console};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'preview.js'),'utf8'),sandbox);
(async()=>{
 await new Promise(r=>setImmediate(r));
 for(const sex of ['female','male'])for(const sequence of ['surface','breach','feeding','missed_water']){
  nodes.sex.value=sex;nodes.sequence.value=sequence;nodes.sequence.onchange();await new Promise(r=>setImmediate(r));
  for(const fraction of [0,.5,.999]){nodes.seek.value=String(fraction);nodes.seek.oninput();await new Promise(r=>setImmediate(r));}
 }
 nodes.sequence.value='clip';nodes.pass.value='normal';nodes.view.value='right';nodes.sequence.onchange();await new Promise(r=>setImmediate(r));
 assert(requested.some(p=>p.includes('normal')));assert(requested.some(p=>p.includes('base')));
 vm.runInContext('time=0;move(-1);if(time!==0)throw Error("negative seek");move(1);if(time<=0)throw Error("next frame");',sandbox);
 const result={status:'PASS',scope:'JavaScript syntax, mocked canvas/DOM selection, referenced files, seek boundaries and data-pass alpha-mask requests',image_requests:requested.length,actual_browser:'NOT_RUN'};
 fs.writeFileSync(path.join(root,'document/preview_validation.json'),JSON.stringify(result,null,2));console.log(result);
})().catch(e=>{console.error(e);process.exitCode=1;});
