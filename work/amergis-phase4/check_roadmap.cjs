const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const {parseHTML}=require('linkedom');
const file=path.resolve(__dirname,'../../outputs/amergis-product-roadmap.html');
const D=JSON.parse(fs.readFileSync(file.replace('.html','.json'),'utf8'));
const {document,window}=parseHTML(fs.readFileSync(file,'utf8'));
const code=document.querySelector('script').textContent;
new vm.Script(code).runInNewContext({document});
const checks=[];
function check(name,fn){fn();checks.push({name,status:'pass'});}
check('Product and feasibility sections populated',()=>{
 assert.equal(document.querySelectorAll('.product').length,D.portfolio.products.length);
 assert.equal(document.querySelectorAll('.reconstruction-area').length,D.reconstruction.areas.length);
 assert.equal(document.querySelectorAll('.arch').length,4);
 assert.equal(document.querySelectorAll('.state-machine').length,4);
});
check('Product search and decision filters',()=>{
 const q=document.getElementById('product-query');q.value='zz-unmatched-zz';q.dispatchEvent(new window.Event('input'));
 assert([...document.querySelectorAll('.product')].every(c=>c.hidden));
 q.value='';q.dispatchEvent(new window.Event('input'));
 const sel=document.getElementById('decision-filter');
 Object.defineProperty(sel,'value',{value:D.portfolio.products[0].decision,writable:true,configurable:true});
 sel.dispatchEvent(new window.Event('change'));
 for(const c of document.querySelectorAll('.product'))assert.equal(!c.hidden,c.dataset.decision===sel.value);
});
check('Artifact links and section anchors resolve',()=>{
 for(const a of document.querySelectorAll('a')){
  const u=a.getAttribute('href');
  if(u.startsWith('https://'))continue;
  if(u.startsWith('#'))assert(document.getElementById(u.slice(1)));
  else assert(fs.existsSync(path.join(path.dirname(file),u)),u);
 }
});
check('Evidence distinctions retained',()=>{
 assert(D.operating_limit.includes('zero-human'));
 assert(D.ats_selection_gate.vendor_status.includes('not selected'));
 assert.equal(D.release_slices.length,5);
 assert(D.not_recoverable_from_public_evidence.length>=4);
});
const result={method:'Local in-memory DOM and artifact checks; no live workflow or rendered browser validation.',checks};
fs.writeFileSync(path.resolve(__dirname,'report-checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
