const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const {parseHTML}=require('linkedom');
const root=path.resolve(__dirname,'../..');
const file=path.join(root,'outputs/school-therapy-requirements.html');
const text=fs.readFileSync(file,'utf8');
const pack=JSON.parse(fs.readFileSync(path.join(root,'outputs/school-therapy-requirements.json'),'utf8'));
const {window}=parseHTML(text);
const document=window.document;
const checks=[];
function check(name,run){run();checks.push({name,status:'pass'});}
for(const el of document.querySelectorAll('script'))vm.runInNewContext(el.textContent,{document});
check('Report renders each requirement, domain object, state model, command and scenario',()=>{
  for(const [selector,count] of [['.requirement',pack.counts.requirements],['.domain-object',pack.counts.objects],['.state-model',pack.counts.state_models],['.command',pack.counts.commands],['.scenario',pack.counts.scenarios],['.source',pack.counts.source_records]])assert.equal(document.querySelectorAll(selector).length,count,selector);
});
check('Requirement text and evidence filters combine correctly',()=>{
 const q=document.getElementById('req-query'); const s=document.getElementById('req-category');
 const visible=()=>[...document.querySelectorAll('.requirement')].filter(x=>!x.hidden);
 q.value='unmatchable-test-string-907';q.dispatchEvent(new window.Event('input'));assert.equal(visible().length,0);
 q.value='';q.dispatchEvent(new window.Event('input'));
 // linkedom has no native select value setter; the report reads the same current value.
 Object.defineProperty(s,'value',{value:'District evidence',writable:true});s.dispatchEvent(new window.Event('change'));
 assert.equal(visible().length,pack.requirements.filter(x=>x.category==='District evidence').length);
 q.value='modality';q.dispatchEvent(new window.Event('input'));assert(visible().length>0);assert(visible().every(x=>x.textContent.toLowerCase().includes('modality')));
 s.value='';q.value='';q.dispatchEvent(new window.Event('input'));assert.equal(visible().length,pack.counts.requirements);
});
check('Local artifacts, section anchors and primary-source URLs resolve structurally',()=>{
 for(const a of document.querySelectorAll('a[href]')){
  const href=a.getAttribute('href');
  if(href.startsWith('#'))assert(document.getElementById(href.slice(1)),href);
  else if(href.startsWith('https://'))assert(new URL(href).hostname);
  else assert(fs.existsSync(path.resolve(path.dirname(file),href)),href);
 }
});
check('Clinical, school-record and future-validation boundaries remain visible',()=>{
 assert(text.includes('Schools and therapists'));
 assert(text.includes('No interviews, outreach, demos, registrations or procurement were performed'));
 assert(text.includes('Specification checks are not product tests'));
 assert(text.includes('dedicated scenario')||text.includes('dedicated case'));
 assert(text.includes('Medicaid'));
 assert(!text.includes('[object Object]'));
 assert(!text.includes('local per-diem RN'));
});
const result={method:'Local in-memory DOM/source checks only; no rendered browser or live integration validation.',checks};
fs.writeFileSync(path.join(__dirname,'report-checks.json'),JSON.stringify(result,null,2)+'\n');
process.stdout.write(JSON.stringify(result,null,2)+'\n');
