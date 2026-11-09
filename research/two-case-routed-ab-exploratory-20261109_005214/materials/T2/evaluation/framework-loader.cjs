"use strict";
const fs=require('fs'), path=require('path'), Module=require('module');
const {findRoot}=require('./native-launch.cjs');
module.exports.load=async function(candidate) {
  const root=findRoot(__dirname), runtimeRoot=path.join(root,'results/student-case-expansion-runtime');
  const req=name=>require(path.join(runtimeRoot,'node_modules',name));
  const {JSDOM}=req('jsdom');
  const dom=new JSDOM('<!doctype html><html><body><div id="app"></div></body></html>');
  for(const key of ['window','document','navigator','Element','HTMLElement','Node','SVGElement'])
    Object.defineProperty(global,key,{value:key==='window'?dom.window:key==='document'?dom.window.document:dom.window[key],configurable:true});
  const config=require('./adapter.json');
  const esbuild=req('esbuild');
  function evaluate(source, filename) {
    const m=new Module(filename,module);m.filename=filename;m.paths=[path.join(runtimeRoot,'node_modules'),...Module._nodeModulePaths(path.dirname(filename))];
    m._compile(source,filename);return m.exports;
  }
  const servicesFile=path.join(candidate,'src/services.js');
  const services=evaluate(esbuild.buildSync({entryPoints:[servicesFile],bundle:true,platform:'node',format:'cjs',write:false,logLevel:'silent'}).outputFiles[0].text,servicesFile);
  let component, framework;
  if(config.runtime==='vue2'||config.runtime==='vue3') {
    framework=req(config.runtime);
    const filename=path.join(candidate,'src/Workspace.vue'), source=fs.readFileSync(filename,'utf8');
    const compiler=req(config.runtime+'/compiler-sfc');
    const parsed=config.runtime==='vue2'?compiler.parse({source,filename}):compiler.parse(source,{filename});
    const descriptor=config.runtime==='vue2'?parsed:parsed.descriptor;
    if(parsed.errors?.length)throw new Error(parsed.errors.join(';'));
    const script=esbuild.buildSync({stdin:{contents:descriptor.script.content,resolveDir:path.dirname(filename),sourcefile:filename},bundle:true,platform:'node',format:'cjs',external:['vue2','vue3'],write:false,logLevel:'silent'}).outputFiles[0].text;
    component=evaluate(script,filename).default;
    if(config.runtime==='vue2') {
      const rendered=compiler.compileTemplate({source:descriptor.template.content,filename,id:'document-port'});
      if(rendered.errors.length)throw new Error(rendered.errors.join(';'));
      const template=esbuild.transformSync(rendered.code+'\nexport {render,staticRenderFns}',{format:'cjs'}).code;
      Object.assign(component,evaluate(template,filename)); framework.config.productionTip=false;framework.config.devtools=false;
    } else component.render=framework.compile(descriptor.template.content);
  } else {
    const filename=path.join(candidate,'src',config.runtime==='react18'?'Workspace.jsx':'workspace.js');
    component=evaluate(esbuild.buildSync({entryPoints:[filename],bundle:true,platform:'node',format:'cjs',external:['react','react-dom','jquery'],write:false,logLevel:'silent'}).outputFiles[0].text,filename);
  }
  return {
    ...services,
    createWorkspace(env) {
      let api,dispose;
      const stop=env.store.subscribe(event=>env.onSaved(event,api));
      if(config.runtime==='vue2') {
        const vm=new framework({...component,propsData:{services:Object.freeze(env)}}).$mount('#app');api=vm;dispose=()=>vm.$destroy();
      } else if(config.runtime==='vue3') {
        const app=framework.createApp(component,{services:env});api=app.mount('#app');dispose=()=>app.unmount();
      } else if(config.runtime==='react18') {
        const React=req('react'), ReactDOM=req('react-dom'), {createRoot}=req('react-dom/client');
        const ref=React.createRef(),app=createRoot(document.querySelector('#app'));
        ReactDOM.flushSync(()=>app.render(React.createElement(component.default,{services:env,ref})));api=ref.current;
        dispose=()=>ReactDOM.flushSync(()=>app.unmount());
      } else { api=component.createWorkspace({element:document.querySelector('#app'),...env});dispose=()=>api.dispose(); }
      const bound={};for(const name of ['open','edit','close','submit'])bound[name]=(...args)=>api[name](...args);
      return {...bound,dispose(){stop();dispose();}};
    },
  };
};
