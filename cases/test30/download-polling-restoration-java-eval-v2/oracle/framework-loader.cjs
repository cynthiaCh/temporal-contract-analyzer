'use strict';
const fs=require('fs'),path=require('path'),Module=require('module');
const {findRoot}=require('./native-launch.cjs');
let sharedDOM;
exports.mount=async function(candidate,config,host,surface,token){
 const root=findRoot(__dirname),runtimeRoot=path.join(root,'results/student-case-expansion-runtime');
 const req=name=>require(path.join(runtimeRoot,'node_modules',name)),{JSDOM}=req('jsdom');
 const dom=sharedDOM||(sharedDOM=new JSDOM('<!doctype html><html><body></body></html>'));
 dom.window.document.body.innerHTML='<div id="app"></div>';
 for(const name of ['window','document','navigator','Element','HTMLElement','Node','SVGElement'])Object.defineProperty(global,name,{value:name==='window'?dom.window:name==='document'?dom.window.document:dom.window[name],configurable:true});
 const esbuild=req('esbuild');
 function evaluate(source,filename){const m=new Module(filename,module);m.filename=filename;m.paths=[path.join(runtimeRoot,'node_modules'),...Module._nodeModulePaths(path.dirname(filename))];m._compile(source,filename);return m.exports;}
 let api,unmount,flush,component;
 const props={host,surface,token};
 if(config.runtime==='vue2'||config.runtime==='vue3'){
  const Vue=req(config.runtime),compiler=req(config.runtime+'/compiler-sfc'),filename=path.join(candidate,'src/Workspace.vue'),source=fs.readFileSync(filename,'utf8');
  const parsed=config.runtime==='vue2'?compiler.parse({source,filename}):compiler.parse(source,{filename}),descriptor=config.runtime==='vue2'?parsed:parsed.descriptor;
  const bundled=esbuild.buildSync({stdin:{contents:descriptor.script.content,resolveDir:path.dirname(filename),sourcefile:filename},bundle:true,platform:'node',format:'cjs',external:['vue2','vue3'],write:false,logLevel:'silent'}).outputFiles[0].text;
  component=evaluate(bundled,filename).default;
  if(config.runtime==='vue2'){
   const tpl=compiler.compileTemplate({source:descriptor.template.content,filename,id:'polling-port'});if(tpl.errors.length)throw new Error(tpl.errors.join(';'));
   Object.assign(component,evaluate(esbuild.transformSync(tpl.code+'\nexport {render,staticRenderFns}',{format:'cjs'}).code,filename));Vue.config.productionTip=false;Vue.config.devtools=false;
   api=new Vue({...component,propsData:props}).$mount('#app');unmount=()=>api.$destroy();
  }else{component.render=Vue.compile(descriptor.template.content);const app=Vue.createApp(component,props);api=app.mount('#app');unmount=()=>app.unmount();}
  flush=async action=>{if(action)action();await Promise.resolve();await Vue.nextTick();await Promise.resolve();};
 }else{
  const filename=path.join(candidate,'src',config.runtime==='react18'?'Workspace.jsx':'workspace.js');
  component=evaluate(esbuild.buildSync({entryPoints:[filename],bundle:true,platform:'node',format:'cjs',external:['react','react-dom','jquery'],write:false,logLevel:'silent'}).outputFiles[0].text,filename);
  if(config.runtime==='react18'){
   const React=req('react'),{createRoot}=req('react-dom/client');global.IS_REACT_ACT_ENVIRONMENT=true;
   flush=async action=>{await React.act(async()=>{if(action)action();await Promise.resolve();await Promise.resolve();});};
   const ref=React.createRef(),app=createRoot(document.querySelector('#app'));await flush(()=>app.render(React.createElement(component.default,{...props,ref})));api=ref.current;unmount=()=>app.unmount();
  }else{api=component.mount(host,surface,token,document.querySelector('#app'));unmount=()=>api.dispose();flush=async action=>{if(action)action();await Promise.resolve();await Promise.resolve();};}
 }
 return {api,unmount,flush,closeDOM:()=>{}};
};
