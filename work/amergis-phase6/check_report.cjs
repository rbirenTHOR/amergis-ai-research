const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {parseHTML}=require('linkedom');
const root=path.resolve(__dirname,'../..'),file=path.join(root,'outputs/school-therapy-pilot-selection.html');
const html=fs.readFileSync(file,'utf8'),pack=JSON.parse(fs.readFileSync(path.join(root,'outputs/school-therapy-pilot-selection.json'),'utf8'));
const {window}=parseHTML(html),document=window.document,checks=[];
for(const el of document.querySelectorAll('script'))vm.runInNewContext(el.textContent,{document});
function check(name,fn){fn();checks.push({name,status:'pass'});}
check('All buyer and evidence records render',()=>{
 assert.equal(document.querySelectorAll('.buyer').length,pack.counts.buyer_records);
 assert.equal(document.querySelectorAll('.source').length,pack.counts.source_records);
 assert.equal(document.querySelectorAll('.credential').length,6);
 assert(!html.includes('[object Object]'));
});
check('Combined search, state and purchasing-route filters',()=>{
 const q=document.getElementById('buyer-query'),s=document.getElementById('buyer-state'),e=document.getElementById('buyer-entry');
 const visible=()=>[...document.querySelectorAll('.buyer')].filter(x=>!x.hidden);
 Object.defineProperty(s,'value',{value:'NY',writable:true});
 Object.defineProperty(e,'value',{value:'',writable:true});
 s.dispatchEvent(new window.Event('change'));
 assert.equal(visible().length,3);
 e.value='Open bid';e.dispatchEvent(new window.Event('change'));assert.equal(visible().length,2);
 q.value='RFP-ER-5-27';q.dispatchEvent(new window.Event('input'));assert.equal(visible().length,1);
 q.value='no-match-check-42911';q.dispatchEvent(new window.Event('input'));assert.equal(visible().length,0);
 document.getElementById('reset').dispatchEvent(new window.Event('click'));assert.equal(visible().length,pack.counts.buyer_records);
});
check('Evidence and buyer navigation open details',()=>{
 for(const id of ['source-CHS05','buyer-MAD01']){
  const a=document.querySelector('a[href="#'+id+'"]');assert(a,id);
  a.dispatchEvent(new window.Event('click',{bubbles:true}));assert(document.getElementById(id).open,id);
 }
});
check('Section, source and local artifact links resolve structurally',()=>{
 for(const a of document.querySelectorAll('a[href]')){
  const href=a.getAttribute('href');
  if(href.startsWith('#'))assert(document.getElementById(href.slice(1)),href);
  else if(href.startsWith('https://'))assert(new URL(href).hostname);
  else assert(fs.existsSync(path.resolve(path.dirname(file),href)),href);
 }
});
check('Material scope and readiness limits are visible',()=>{
 for(const text of ['Target selection, not bid readiness','In-person only','five-year','RSA','not a buyer commitment','No buyer contact','Compact membership is not a practice privilege'])assert(html.includes(text),text);
});
const result={status:'pass',method:'Local in-memory DOM/source checks; not rendered-browser verification or live procurement testing.',checks};
fs.writeFileSync(path.join(__dirname,'report-checks.json'),JSON.stringify(result,null,2)+'\n');
process.stdout.write(JSON.stringify(result,null,2)+'\n');
