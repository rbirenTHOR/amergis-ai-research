const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const {parseHTML}=require('linkedom');
const file=path.resolve(__dirname,'../../outputs/amergis-api-reconstruction.html');
const {document,window}=parseHTML(fs.readFileSync(file,'utf8'));
const D=JSON.parse(document.getElementById('report-data').textContent);
const js=[...document.querySelectorAll('script')].find(s=>!s.type).textContent;
new vm.Script(js).runInNewContext({document,console});
const checks=[];
function check(name,fn){fn();checks.push({name,status:'pass'});}
function click(s){const e=document.querySelector(s);assert(e,s);e.dispatchEvent(new window.Event('click'));}
check('All platform, source and workflow rows render',()=>{
  assert.equal(document.querySelectorAll('[data-platform]').length,12);
  assert.equal(document.querySelectorAll('#lanes .card').length,7);
  assert.equal(document.querySelectorAll('#sources .source-card').length,65);
  assert.equal(document.querySelectorAll('#endpoint-examples tr').length,15);
});
check('Every platform selection renders its matching detail',()=>{
  for(const p of D.platforms){
    click(`[data-platform="${p.id}"]`);
    assert(document.getElementById('platform-detail').textContent.includes(p.name));
    assert.equal(document.querySelectorAll('[data-platform][aria-pressed="true"]').length,1);
  }
});
check('Tabs select one panel',()=>{
  for(const b of document.querySelectorAll('[data-tab]')){
    click(`[data-tab="${b.dataset.tab}"]`);
    assert.equal(document.querySelectorAll('.panel.active').length,1);
    assert(document.getElementById(b.dataset.tab).classList.contains('active'));
  }
});
check('Source filter finds Nursys',()=>{
  const el=document.getElementById('source-search');
  el.value='Nursys';el.dispatchEvent(new window.Event('input'));
  assert.equal(document.querySelectorAll('#sources .source-card').length,3);
});
check('All artifact links exist and external URLs are HTTPS',()=>{
  for(const a of document.querySelectorAll('a')){
    const href=a.getAttribute('href');
    if(href.startsWith('https://')) continue;
    assert(!href.includes(':'),href);
    assert(fs.existsSync(path.resolve(path.dirname(file),href)),href);
  }
});
check('New office data reconciles to source totals',()=>{
  assert.equal(D.public_locations.records.length,61);
  assert.equal(D.public_locations.counts.with_address,61);
  assert.equal(D.public_locations.counts.with_public_branch_email,59);
  assert.equal(D.public_locations.source_api_total_pages,1);
});
check('No copied tokens and appropriate event-consumption distinction',()=>{
  assert(!JSON.stringify(D).includes('pk_live_'));
  assert(!JSON.stringify(D).includes('__RequestVerificationToken'));
  assert(document.getElementById('endpoint-examples').textContent.includes('consumes and purges'));
  assert.equal(D.counts.authenticated_sessions,0);
});
const result={method:'Local in-memory DOM source check; not rendered browser validation or live integration testing.',checks};
fs.writeFileSync(path.resolve(__dirname,'report-checks.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
