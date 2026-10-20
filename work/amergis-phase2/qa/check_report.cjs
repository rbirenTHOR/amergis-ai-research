const fs = require("fs");
const vm = require("vm");
const assert = require("assert");
const path = require("path");
const {parseHTML} = require("linkedom");

const output = path.resolve(__dirname,"../../..","outputs/amergis-operating-blueprint.html");
const {document,window}=parseHTML(fs.readFileSync(output,"utf8"));
const code=[...document.querySelectorAll("script")].find(s=>!s.type).textContent;
new vm.Script(code).runInNewContext({document,console});
const checks=[];
function check(name,fn){fn();checks.push({name,status:"pass"});}
function click(selector){const el=document.querySelector(selector);assert(el,selector);el.dispatchEvent(new window.Event("click"));}
function select(id,value){const el=document.getElementById(id);Object.defineProperty(el,"value",{value,writable:true,configurable:true});el.dispatchEvent(new window.Event("change"));}
check("Initial data and task rendering",()=>{
 assert.equal(document.querySelectorAll("#task-rows tr").length,63);
 assert.equal(document.querySelectorAll("#stage-list button").length,12);
 assert.equal(document.querySelectorAll("#capabilities .cap-card").length,11);
 assert.equal(document.querySelectorAll("#contract-rows tr").length,6);
 assert.equal(document.querySelectorAll("#contract-rules .rule").length,57);
});
check("Tab selection",()=>{
 click('[data-panel="functions"]');
 assert(document.getElementById("functions").classList.contains("active"));
 assert(!document.getElementById("overview").classList.contains("active"));
});
check("Authority filter",()=>{
 select("class-filter","A");
 assert.equal(document.querySelectorAll("#task-rows tr").length,26);
 select("class-filter","B");
 assert.equal(document.querySelectorAll("#task-rows tr").length,23);
 select("class-filter","C");
 assert.equal(document.querySelectorAll("#task-rows tr").length,14);
 select("class-filter","");
});
check("Payroll task detail preserves worked-time distinction",()=>{
 click('[data-task="T050"]');
 const text=document.getElementById("task-detail").textContent;
 assert(/disputed|pending-approval/.test(text));
 assert(/billing/i.test(text));
});
check("Workflow readiness gate",()=>{
 click('[data-stage="W06"]');
 assert(document.getElementById("stage-detail").textContent.includes("T063"));
 click('[data-stage="W07"]');
 assert(document.getElementById("stage-detail").textContent.includes("authorized human owner"));
});
check("Contract filter and corrected billing rules",()=>{
 select("contract-filter","C06");
 const text=document.getElementById("contract-rules").textContent;
 assert(text.includes("CR051"));
 assert(/processing/i.test(text));
 assert(!text.includes("CR001"));
});
check("Text search",()=>{
 const q=document.getElementById("task-search");
 q.value="credential";q.dispatchEvent(new window.Event("input"));
 assert(document.getElementById("task-count").textContent.startsWith("7 of"));
});
check("Download links exist",()=>{
 for(const a of document.querySelectorAll(".download a")){
  assert(fs.existsSync(path.join(path.dirname(output),a.getAttribute("href"))));
 }
});
fs.writeFileSync(path.join(__dirname,"report-checks.json"),JSON.stringify({method:"Local in-memory DOM source test; no browser or live application interaction.",checks},null,2));
console.log(JSON.stringify(checks,null,2));
