'use strict';
const fs=require('fs'),path=require('path'),Module=require('module'),{findRoot}=require('./native-launch.cjs');
exports.load=async function(candidate){
 const root=findRoot(__dirname),runtimeRoot=path.join(root,'results/student-case-expansion-runtime'),req=name=>require(path.join(runtimeRoot,'node_modules',name));
 const config=require('./adapter.json'),esbuild=req('esbuild');
 let dom;if(config.runtime!=='vanilla-js'){
 dom=new(req('jsdom').JSDOM)('<!doctype html><html><body></body></html>');
 for(const key of ['window','document','navigator','Element','HTMLElement','Node','SVGElement'])Object.defineProperty(global,key,{value:key==='window'?dom.window:key==='document'?dom.window.document:dom.window[key],configurable:true});}
 function evaluate(code,file){const m=new Module(file,module);m.filename=file;m.paths=[path.join(runtimeRoot,'node_modules'),...Module._nodeModulePaths(path.dirname(file))];m._compile(code,file);return m.exports;}
 function bundle(file){return evaluate(esbuild.buildSync({entryPoints:[file],bundle:true,platform:'node',format:'cjs',external:['vue2','vue3','react','react-dom','jquery'],write:false,logLevel:'silent'}).outputFiles[0].text,file);}
 let component,framework;
 if(['vue2','vue3'].includes(config.runtime)){
 framework=req(config.runtime);const compiler=req(config.runtime+'/compiler-sfc'),file=path.join(candidate,'src/Workspace.vue'),source=fs.readFileSync(file,'utf8'),parsed=config.runtime==='vue2'?compiler.parse({source,filename:file}):compiler.parse(source,{filename:file}),d=config.runtime==='vue2'?parsed:parsed.descriptor;
 const code=esbuild.buildSync({stdin:{contents:d.script.content,resolveDir:path.dirname(file),sourcefile:file},bundle:true,platform:'node',format:'cjs',external:['vue2','vue3'],write:false,logLevel:'silent'}).outputFiles[0].text;component=evaluate(code,file).default;
 if(config.runtime==='vue2'){const t=compiler.compileTemplate({source:d.template.content,filename:file,id:'cached-feed'});if(t.errors.length)throw Error(t.errors.join(';'));Object.assign(component,evaluate(esbuild.transformSync(t.code+'\nexport {render,staticRenderFns}',{format:'cjs'}).code,file));framework.config.productionTip=false;framework.config.devtools=false;}else component.render=framework.compile(d.template.content);
 }else component=bundle(path.join(candidate,'src',config.runtime==='react18'?'Workspace.jsx':'workspace.js'));
 const configRuntime=config.runtime;const instances=[];
 return {createController(config,env){
 const host={config,env};let api,dispose;
 const element=document.body.appendChild(document.createElement('div'));
 if(configRuntime==='vue2'){const vm=new framework({...component,propsData:{host}}).$mount(element);api=vm;dispose=()=>vm.$destroy();}
 else if(configRuntime==='vue3'){const app=framework.createApp(component,{host});api=app.mount(element);dispose=()=>app.unmount();}
 else if(configRuntime==='react18'){const React=req('react'),ReactDOM=req('react-dom'),{createRoot}=req('react-dom/client'),ref=React.createRef(),app=createRoot(element);ReactDOM.flushSync(()=>app.render(React.createElement(component.default,{host,ref})));let retained=ref.current;api={command:(...a)=>{if(ref.current)retained=ref.current;return retained.command(...a);}};dispose=()=>ReactDOM.flushSync(()=>app.unmount());}
 else{api=component.createController({...host,element});dispose=()=>api.dispose();}
 let disposed=false;const retire=()=>{if(!disposed){disposed=true;dispose();}};instances.push(retire);
 return {call:(name,...args)=>api.command(name,args),dispose:retire};
 },finish(){for(const f of instances)f();dom.window.close();}};
};
