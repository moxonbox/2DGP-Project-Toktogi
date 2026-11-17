import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const html=fs.readFileSync(path.join(root,'PardosaIdlePreview.html'),'utf8');
const script=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const manifest=JSON.parse(html.match(/<script id="manifest"[^>]*>([\s\S]*?)<\/script>/)[1]);
const sources=JSON.parse(html.match(/<script id="images"[^>]*>([\s\S]*?)<\/script>/)[1]);
const elements={};
for(const id of ['play','view','pass','scale','fps','frame','index','light','flat','status']){
  elements[id]={value:'0',checked:false,textContent:''};
}
Object.assign(elements.view,{value:'left'});
Object.assign(elements.pass,{value:'sprite'});
Object.assign(elements.scale,{value:'3'});
Object.assign(elements.fps,{value:'60'});
Object.assign(elements.light,{value:'-35'});
let activePass='sprite';
const context={
  clearRect(){},drawImage(image){activePass=image.pass;},putImageData(){},
  getImageData(){
    const data=new Uint8ClampedArray(640*640*4);
    const values={base:[120,80,50,255],normal:[180,128,240,255],ao:[230,230,230,255],rm:[140,0,0,255]};
    for(let i=0;i<data.length;i+=4)data.set(values[activePass]||[70,40,20,255],i);
    return {data};
  }
};
elements.canvas={style:{},getContext(){return context;}};
class MockImage{
  set src(value){this.pass=Object.keys(sources).find(k=>sources[k]===value).split('_').at(-1);queueMicrotask(()=>this.onload());}
}
const sandbox={console,Image:MockImage,Uint8ClampedArray,requestAnimationFrame(){},
  document:{getElementById(id){return elements[id];},createElement(){return elements.canvas;},
    querySelector(selector){return {textContent:JSON.stringify(selector==='#manifest'?manifest:sources)};}}};
vm.createContext(sandbox);
new vm.Script(script).runInContext(sandbox);
await new Promise(resolve=>setImmediate(resolve));
for(let i=0;i<24;i++)assert.equal(vm.runInContext(`frameAt(${i}/12)`,sandbox),i);
assert.equal(vm.runInContext('frameAt(2)',sandbox),0);
assert.equal(vm.runInContext('frameAt(-1/12)',sandbox),23);
elements.play.onclick();
assert.equal(vm.runInContext('playing',sandbox),false);
elements.frame.value='17';elements.frame.oninput();
assert.equal(vm.runInContext('frameAt(time)',sandbox),17);
elements.pass.value='relit';elements.light.value='-80';elements.pass.oninput();
const a=vm.runInContext("relight('left',0).data[0]",sandbox);
elements.light.value='80';
const b=vm.runInContext("relight('left',0).data[0]",sandbox);
assert.notEqual(a,b);
elements.flat.checked=true;
const c=vm.runInContext("relight('left',0).data[0]",sandbox);
assert.notEqual(b,c);
assert.equal(Object.keys(sources).length,12);
const reportPath=path.join(root,'2D/idle-r02/package_validation.json');
const report=JSON.parse(fs.readFileSync(reportPath,'utf8'));
report.preview_javascript='PASS syntax, loop boundaries, seeking, pause, light and flat-Normal controls with synthetic pixels';
report.browser_visual_check='NOT_RUN';
fs.writeFileSync(reportPath,JSON.stringify(report,null,2));
console.log(report.preview_javascript);
