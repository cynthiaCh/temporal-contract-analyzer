'use strict';
const path=require('path'),Module=require('module'),{findRoot}=require('./native-launch.cjs');
exports.load=async function(candidate){
 process.env.FTC_NATIVE_CANDIDATE=candidate;require('./native-rxjs-preload.cjs');
 const root=findRoot(__dirname),runtime=path.join(root,'results/student-case-expansion-runtime'),esbuild=require(path.join(runtime,'node_modules/esbuild')),file=path.join(candidate,'src/consumer.js');
 const code=esbuild.buildSync({entryPoints:[file],bundle:true,platform:'node',format:'cjs',write:false,logLevel:'silent'}).outputFiles[0].text;
 const mod=new Module(file,module);mod.filename=file;mod._compile(code,file);const controllers=[];
 return{createController(config,env){const a=mod.exports.createController({config,env});controllers.push(a);return {call:(name,...args)=>a.command(name,args),dispose:()=>a.dispose()};},finish(){controllers.forEach(a=>a.dispose());}};
};
