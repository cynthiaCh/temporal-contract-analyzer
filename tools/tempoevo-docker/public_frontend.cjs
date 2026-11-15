// Framework mounting and candidate imports only. No benchmark oracle imports.
'use strict';
const fs=require('fs'),path=require('path'),Module=require('module');
const deps='/opt/swe-tempoc/results/student-case-expansion-runtime/node_modules';
const req=name=>require(path.join(deps,name));
module.exports=function(candidate,runtime,family){
 const {JSDOM}=req('jsdom'),dom=new JSDOM('<html><body></body></html>');
 for(const key of ['window','document','navigator','Element','HTMLElement','Node','SVGElement'])Object.defineProperty(global,key,{value:key==='window'?dom.window:key==='document'?dom.window.document:dom.window[key],configurable:true});
 const esbuild=req('esbuild'),cache=new Map(),externals=['react','react-dom','react-dom/client','jquery','vue2','vue3'];
 function evaluate(source,filename){const m=new Module(filename,module);m.filename=filename;m.paths=[deps,...Module._nodeModulePaths(path.dirname(filename))];m._compile(source,filename);return m.exports;}
 function load(file){if(cache.has(file))return cache.get(file);const filename=path.join(candidate,'src',file);const value=evaluate(esbuild.buildSync({entryPoints:[filename],bundle:true,platform:'node',format:'cjs',external:externals,nodePaths:[deps],write:false,logLevel:'silent'}).outputFiles[0].text,filename);cache.set(file,value);return value;}
 let component;
 function mounted(prop,value){
  const element=document.createElement('div');document.body.append(element);let api,unmount,flush=fn=>fn();
  if(runtime==='react18'){
   const React=req('react'),ReactDOM=req('react-dom'),{createRoot}=req('react-dom/client');flush=ReactDOM.flushSync;
   if(!component)component=load('Workspace.jsx').default;
   const ref=React.createRef(),root=createRoot(element);flush(()=>root.render(React.createElement(component,{[prop]:value,ref})));api=ref.current;unmount=()=>flush(()=>root.unmount());
  }else{
   const framework=req(runtime);
   if(!component){
    const filename=path.join(candidate,'src/Workspace.vue'),source=fs.readFileSync(filename,'utf8'),compiler=req(runtime+'/compiler-sfc');
    const parsed=runtime==='vue2'?compiler.parse({source,filename}):compiler.parse(source,{filename});const descriptor=runtime==='vue2'?parsed:parsed.descriptor;
    if(parsed.errors?.length)throw Error(parsed.errors.join(';'));
    component=evaluate(esbuild.buildSync({stdin:{contents:descriptor.script.content,resolveDir:path.dirname(filename),sourcefile:filename},bundle:true,platform:'node',format:'cjs',external:externals,nodePaths:[deps],write:false,logLevel:'silent'}).outputFiles[0].text,filename).default;
    if(runtime==='vue2'){
     const template=compiler.compileTemplate({source:descriptor.template.content,filename,id:'public-checks'});if(template.errors.length)throw Error(template.errors.join(';'));
     Object.assign(component,evaluate(esbuild.transformSync(template.code+'\nexport {render,staticRenderFns}',{format:'cjs'}).code,filename));framework.config.productionTip=false;framework.config.devtools=false;
    }else component.render=framework.compile(descriptor.template.content);
   }
   if(runtime==='vue2'){api=new framework({...component,propsData:{[prop]:value}}).$mount(element);unmount=()=>api.$destroy();}
   else{const app=framework.createApp(component,{[prop]:value});api=app.mount(element);unmount=()=>app.unmount();}
  }
  const wrapped={};for(const name of ['open','edit','close','submit','select','retry','hide','snapshot','subscribe','unsubscribe','online','focus','command'])if(typeof api[name]==='function')wrapped[name]=(...args)=>{let answer;flush(()=>{answer=api[name](...args);});return answer;};
  let disposed=false;wrapped.dispose=()=>{if(disposed)return;disposed=true;if(typeof api.dispose==='function')flush(()=>api.dispose());unmount();element.remove();};return wrapped;
 }
 const frontend=['react18','vue2','vue3'].includes(runtime);
 if(family==='query')return{createClient(host,initial){const session=new (load('session.js').Session)(host,initial);if(frontend)return mounted('session',session);if(runtime==='jquery')return load('workspace.js').mount(session,document.body.appendChild(document.createElement('div')));return session;}};
 if(family==='transfer')return{createTransferWorkspace(host){if(frontend)return mounted('host',host);const w=load('workspace.js');if(w.createTransferWorkspace)return w.createTransferWorkspace(host);return w.mount(host,null,null,document.body.appendChild(document.createElement('div')));}};
 if(family==='generator'||family==='subscription')return{createController(host){return mounted('host',host);}};
 const services=load('services.js');return{...services,createWorkspace(env){if(frontend)return mounted('services',env);return load('workspace.js').createWorkspace({element:document.body.appendChild(document.createElement('div')),...env});}};
};
