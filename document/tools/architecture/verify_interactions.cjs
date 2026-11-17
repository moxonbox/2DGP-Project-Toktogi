// Exercise the delivered script with the DOM APIs it uses.
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../..','ToktogiProjectArchitecture.html'),'utf8');
const payload=html.match(/<script id="atlas-data" type="application\/json">(.*?)<\/script>/s)[1];
class Element {
  constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.attrs={};this.events={};this.textContent='';this.value='';}
  addEventListener(name,fn){this.events[name]=fn;}
  dispatchEvent(event){this.events[event.type]?.({preventDefault(){},...event,target:this});}
  click(){this.dispatchEvent({type:'click'});}
  setAttribute(name,value){this.attrs[name]=value;}
  removeAttribute(name){delete this.attrs[name];}
  replaceChildren(...children){this.children=children;}
  append(...children){this.children.push(...children);}
  querySelector(){return new Element();}
  focus(){}
}
const elements=Object.fromEntries([...html.matchAll(/<([\w]+)[^>]*?\bid="([\w-]+)"/g)].map(m=>[m[2],new Element(m[1])]));
elements['atlas-data'].textContent=payload;
const data=JSON.parse(payload);
elements.clip.value=data.videos[0].id;
elements.fps.value='60';
const recordings=[];
elements.sprite.getContext=()=>({clearRect(){},drawImage(_img,...args){recordings.push(args);}});
const arrows=[];
elements.edges.getContext=()=>({setTransform(){},beginPath(){},moveTo(){},lineTo(){},stroke(){arrows.push(1);},closePath(){},fill(){}});
elements.edges.getBoundingClientRect=()=>({top:0,left:0,width:650,height:160});
const buttons=type=>[...html.matchAll(new RegExp(`<button[^>]*data-${type}="([A-Za-z]+)"`,'g'))].map(m=>{
  const item=new Element('button');item.dataset[type]=m[1];return item;
});
const sidebar=[...html.match(/<nav aria-label="안내서 탐색">(.*?)<\/nav>/s)[1].matchAll(/href="(#[a-z]+)"/g)].map(m=>{
  const a=new Element('a');a.hash=m[1];return a;
});
const controls={'[data-node]':buttons('node'),'[data-state]':buttons('state'),'.sidebar nav a':sidebar};
const positions={entry:[0,0],clock:[0,1],rules:[0,2],motion:[0,3],render:[0,4],author:[1,0],assets:[1,1],course:[1,2],replay:[1,4]};
controls['[data-node]'].forEach(n=>{
  const [row,column]=positions[n.dataset.node];
  n.getBoundingClientRect=()=>({top:80*row,left:130*column,width:115,height:60});
});
const document={
  getElementById:id=>elements[id], createElement:tag=>new Element(tag),
  querySelectorAll:selector=>controls[selector]||[], addEventListener(){}
};
class EmbeddedImage {
  set src(value){assert.match(value,/^data:image\/png;base64,/);this.onload();}
}
const handlers={};
const location={hash:''};
const scope=vm.createContext({document,window:{addEventListener(name,fn){handlers[name]=fn;},scrollTo(){},print(){}},
  location,history:{pushState(_,__,url){location.hash=url;}},Image:EmbeddedImage,
  performance:{now:()=>0},requestAnimationFrame:()=>1,cancelAnimationFrame(){}});
vm.runInContext(html.match(/<script>(.*?)<\/script>/s)[1],scope);
const checks=[];
function test(name,fn){fn();checks.push(name);}
test('default sprite draws',()=>assert.equal(recordings.length,1));
test('first view is the complete architecture diagram',()=>{
  assert.equal(elements.architecture.hidden,false);
  assert.equal(elements.controls.hidden,true);
  vm.runInContext('drawConnections()',scope);
  assert.equal(arrows.length,8);
});
test('node inspector and source coordinates',()=>{
  controls['[data-node]'].find(b=>b.dataset.node==='assets').click();
  assert.equal(elements['node-title'].textContent,'에셋 저장소');
  assert.equal(elements['node-sources'].children.length,3);
  assert.equal(controls['[data-node]'].find(b=>b.dataset.node==='clock').dataset.related,'false');
  elements['node-reset'].click();
  assert.ok(controls['[data-node]'].every(b=>b.dataset.related==='true'));
});
test('behavior states',()=>{
  const edgeKeys=()=>elements['state-transitions'].children.flatMap(li=>li.children.filter(el=>el.tag==='kbd').map(el=>el.textContent));
  assert.deepEqual(edgeKeys(),['←','→','Space','E','F','G','X']);
  controls['[data-state]'].find(b=>b.dataset.state==='Combat').click();
  assert.match(elements['state-name'].textContent,/^Combat/);
  assert.equal(elements['state-transitions'].children.length,3);
  assert.deepEqual(edgeKeys(),['Space']);
  controls['[data-state]'].find(b=>b.dataset.state==='Interact').click();
  const attack = elements['state-transitions'].children.find(li=>li.children.some(el=>el.textContent.includes('→ Combat')));
  assert.ok(attack.children.some(el=>el.tag==='kbd' && el.textContent==='X'));
});
test('specifications navigation',()=>{
  sidebar.find(a=>a.hash==='#specs').click();
  assert.equal(elements.specs.hidden,false);
  assert.equal(elements.states.hidden,true);
});
test('navigation current',()=>{
  sidebar.find(a=>a.hash==='#motion').click();
  assert.equal(sidebar.filter(a=>a.attrs['aria-current']==='page').length,1);
  assert.equal(sidebar.find(a=>a.attrs['aria-current']==='page').hash,'#motion');
  assert.equal(location.hash,'#motion');
  assert.equal(elements.architecture.hidden,true);
  assert.equal(elements.motion.hidden,false);
  location.hash='#states';handlers.hashchange();
  assert.equal(elements.motion.hidden,true);
  assert.equal(elements.states.hidden,false);
});
test('module search by symbol',()=>{
  elements['module-search'].value='MotionSet';elements['module-search'].dispatchEvent({type:'input'});
  assert.equal(elements.modules.children.length,1);
  assert.equal(elements.modules.children[0].children[0].textContent,'motion.py');
  elements['module-search'].value='Game.try_turn';elements['module-search'].dispatchEvent({type:'input'});
  assert.equal(elements.modules.children.length,1);
  assert.equal(elements.modules.children[0].children[0].href,'#files/game.py');
});
test('framework and direct module links',()=>{
  sidebar.find(a=>a.hash==='#framework').click();
  assert.equal(elements.framework.hidden,false);
  location.hash='#files/motion.py';handlers.hashchange();
  assert.equal(elements.framework.hidden,true);
  assert.equal(elements['module-source'].href,'../prototype/motion.py');
  assert.ok(elements['module-in'].children.some(li=>li.children[0].href==='#files/game.py'));
  assert.equal(elements['module-out'].children[0].textContent,'없음');
  assert.match(elements['module-definitions'].children[0].children[0].textContent,/class Track · L6/);
  elements['module-file'].value='input_clock.py';elements['module-file'].dispatchEvent({type:'change'});
  assert.match(location.hash,/#?files\/input_clock.py/);
  handlers.hashchange();
  assert.equal(elements['module-source'].textContent,'input_clock.py');
  assert.match(elements['module-definitions'].children[0].children[0].textContent,/class SDLEvent\(ctypes\.Union\)/);
});
test('clip switch and nearest-cell seeking',()=>{
  elements.clip.value='game_ground_spin_right';elements.clip.dispatchEvent({type:'change'});
  assert.equal(elements.seek.max,62);
  assert.match(elements['clip-time'].textContent,/1\.550/);
  elements.next.click();assert.equal(elements.seek.value,2);
  elements.seek.value='62';elements.seek.dispatchEvent({type:'input'});
  assert.equal(elements.seek.value,62);
});
test('10 fps resumes, advances and stops at last cell',()=>{
  elements.fps.value='10';elements.prev.click();elements.play.click();
  vm.runInContext('tick(200)',scope);
  assert.equal(elements.seek.value,62);
  assert.equal(elements.play.textContent,'다시 재생');
  elements.play.click();
  vm.runInContext('tick(0);tick(50);',scope);assert.equal(elements.seek.value,1);
  vm.runInContext('tick(100);',scope);assert.equal(elements.seek.value,5);
});
test('leaving the motion view pauses playback',()=>{
  sidebar.find(a=>a.hash==='#motion').click();
  sidebar.find(a=>a.hash==='#files').click();
  assert.equal(vm.runInContext('player.running',scope),false);
});
console.log(JSON.stringify({checks,passed:checks.length}));
