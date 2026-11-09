// Offline DOM-logic smoke checks. This does not execute anything from the ZIP.
const fs=require('fs'),vm=require('vm'),path=require('path');
const dir=__dirname,html=fs.readFileSync(path.join(dir,'ranking.html'),'utf8');
const blocks=[...html.matchAll(/<script(?: [^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
class Element{constructor(){this.children=[];this.value='';this.textContent='';this.style={}}appendChild(x){this.children.push(x);return x}replaceChildren(...x){this.children=x}addEventListener(){}click(){}}
const nodes={};for(const n of ['model','effort','condition','variant','search','minn','sort','cards','body','caption','download','dataset'])nodes[n]=new Element();nodes.dataset.textContent=blocks[0];nodes.minn.value='0';nodes.sort.value='hard';
const document={getElementById:n=>nodes[n],createElement:()=>new Element(),createTextNode:t=>({textContent:t})};const ctx=vm.createContext({document,console,setTimeout,URL:{},Blob});vm.runInContext(blocks[1],ctx);
function expect(v,msg){if(!v)throw Error(msg)}
expect(nodes.body.children.length===249,'Complete table must contain every case');expect(nodes.cards.children[2].children[0].textContent==='68.11%','Default pooled rate must match the CSV analysis');
const unknown=nodes.body.children.find(r=>r.children[1].textContent==='publish-validity-preview-request-latent-vanilla');expect(unknown.children[3].textContent==='N/A','Zero denominator must display N/A');
nodes.minn.value='10';vm.runInContext('render()',ctx);expect(nodes.body.children.length===242,'Minimum sample filter');expect(nodes.body.children[0].children[1].textContent==='review-confirmation-binding-react','Hardest case at n >= 10');
nodes.minn.value='0';nodes.model.value='gpt-5.6-terra';nodes.effort.value='low';nodes.search.value='query-paused-initial-fetch-10266-python3';vm.runInContext('render()',ctx);expect(nodes.body.children.length===1,'Model, effort and search filters');expect(nodes.body.children[0].children[2].textContent==='0 / 1','Matched stratum count');
const result={passed:true,checks:7,full_cases:249,min_10_valid_cases:242,default_pooled_rate:'68.11%',matched_terra_low_query_python:'0 / 1',scope:'Offline DOM-logic smoke check, not a full browser layout test'};fs.writeFileSync(path.join(dir,'html-validation.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
