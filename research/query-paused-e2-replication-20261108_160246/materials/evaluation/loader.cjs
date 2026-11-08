'use strict';
const fs=require('fs'),path=require('path'),Module=require('module'),{findRoot,launch}=require('./native-launch.cjs');let dom;
exports.load=function(candidate,oracle){const config=require(path.join(oracle,'adapter.json'));
 if(['java','python3','php','ruby','go'].includes(config.runtime)){const options=launch(candidate,oracle);return require('./bridge.cjs').connect(options.command,options.env);}
 const runtime=path.join(findRoot(oracle),'results/student-case-expansion-runtime'),req=name=>require(path.join(runtime,'node_modules',name)),{JSDOM}=req('jsdom');
 dom=dom||new JSDOM('<!doctype html><html><body></body></html>');dom.window.document.body.innerHTML='';
 for(const name of ['window','document','navigator','Element','HTMLElement','Node','SVGElement'])Object.defineProperty(global,name,{value:name==='window'?dom.window:name==='document'?dom.window.document:dom.window[name],configurable:true});
 const esbuild=req('esbuild'),mounted=[];
 function evaluate(source,filename){const m=new Module(filename,module);m.filename=filename;m.paths=[path.join(runtime,'node_modules'),...Module._nodeModulePaths(path.dirname(filename))];m._compile(source,filename);return m.exports;}
 function bundle(file){return evaluate(esbuild.buildSync({entryPoints:[file],bundle:true,platform:'node',format:'cjs',external:['vue2','vue3','react','react-dom','jquery'],write:false,logLevel:'silent'}).outputFiles[0].text,file);}
 const Session=bundle(path.join(candidate,'src/session.js')).Session;
 if(config.runtime==='vanilla-js')return {createClient:(host,initial)=>new Session(host,initial),close(){}};
 let component;
 if(config.runtime==='vue2'||config.runtime==='vue3'){
  const compiler=req(config.runtime+'/compiler-sfc'),filename=path.join(candidate,'src/Workspace.vue'),source=fs.readFileSync(filename,'utf8'),parsed=config.runtime==='vue2'?compiler.parse({source,filename}):compiler.parse(source,{filename}),descriptor=config.runtime==='vue2'?parsed:parsed.descriptor;
  component=evaluate(esbuild.buildSync({stdin:{contents:descriptor.script.content,resolveDir:path.dirname(filename),sourcefile:filename},bundle:true,platform:'node',format:'cjs',external:['vue2','vue3'],write:false,logLevel:'silent'}).outputFiles[0].text,filename).default;
  if(config.runtime==='vue2'){const tpl=compiler.compileTemplate({source:descriptor.template.content,filename,id:'transfer-port'});if(tpl.errors.length)throw Error(tpl.errors.join(';'));Object.assign(component,evaluate(esbuild.transformSync(tpl.code+'\nexport {render,staticRenderFns}',{format:'cjs'}).code,filename));}
  else component.render=req('vue3').compile(descriptor.template.content);
 }else component=bundle(path.join(candidate,'src',config.runtime==='react18'?'Workspace.jsx':'workspace.js'));
 return {createClient(host,initial){const session=new Session(host,initial);const element=document.createElement('div');document.body.append(element);let api,unmount;
  if(config.runtime==='vue2'){const Vue=req('vue2');Vue.config.productionTip=false;Vue.config.devtools=false;api=new Vue({...component,propsData:{session}}).$mount(element);unmount=()=>api.$destroy();}
  else if(config.runtime==='vue3'){const Vue=req('vue3'),app=Vue.createApp(component,{session:Vue.markRaw(session)});api=app.mount(element);unmount=()=>app.unmount();}
  else if(config.runtime==='react18'){const React=req('react'),{createRoot}=req('react-dom/client'),{flushSync}=req('react-dom'),ref=React.createRef(),app=createRoot(element);flushSync(()=>app.render(React.createElement(component.default,{host,ref})));api=ref.current;unmount=()=>flushSync(()=>app.unmount());}
  else{api=component.mount(session,element);unmount=()=>api.dispose();}
  let ended=false;const finish=()=>{if(!ended){ended=true;unmount();}};mounted.push({api,unmount:finish,element});return api;
 },async flush(){if(config.runtime==='vue2'||config.runtime==='vue3')await req(config.runtime).nextTick();else if(config.runtime==='react18'){await new Promise(resolve=>setImmediate(resolve));req('react-dom').flushSync(()=>{});}await Promise.resolve();},rendered(){return document.body.textContent;},unmount(){for(const x of mounted)x.unmount();},close(){for(const x of mounted){x.unmount();x.element.remove();}}};
};
