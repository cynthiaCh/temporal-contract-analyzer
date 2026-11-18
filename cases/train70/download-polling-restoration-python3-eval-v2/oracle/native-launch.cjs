"use strict";
const fs=require('fs'),path=require('path'),cp=require('child_process'),crypto=require('crypto');
function findRoot(start) {
  let root=start;
  while(!fs.existsSync(path.join(root,'casecatalog.py'))) { const next=path.dirname(root);if(next===root)throw new Error('repository root not found');root=next; }
  return root;
}
exports.findRoot=findRoot;
exports.launch=function(candidate,oracle) {
  const root=findRoot(oracle), runtime=path.join(root,'results/student-case-expansion-runtime/native'), config=require(path.join(oracle,'adapter.json'));
  const env={...process.env,PYTHONDONTWRITEBYTECODE:'1'};
  if(config.runtime==='python3')return {command:['python3','-B',path.join(oracle,'driver.py'),candidate],env};
  if(config.runtime==='php')return {command:[path.join(runtime,'usr/bin/php7.4'),'-n','-d','extension='+path.join(runtime,'usr/lib/php/20190902/json.so'),path.join(oracle,'driver.php'),candidate],env};
  if(config.runtime==='ruby') {
    env.LD_LIBRARY_PATH=path.join(runtime,'usr/lib/x86_64-linux-gnu');
    env.RUBYLIB=[path.join(runtime,'usr/lib/ruby/2.7.0'),path.join(runtime,'usr/lib/x86_64-linux-gnu/ruby/2.7.0')].join(':');
    return {command:[path.join(runtime,'usr/bin/ruby2.7'),path.join(oracle,'driver.rb'),candidate],env};
  }
  const file=config.runtime==='java'?'Workflow.java':'workflow.go',driver=config.runtime==='java'?'Driver.java':'driver.go';
  const files=[fs.readFileSync(path.join(candidate,'src',file)),fs.readFileSync(path.join(oracle,driver))];
  const hash=crypto.createHash('sha256').update(Buffer.concat(files)).digest('hex');
  const build=path.join(root,'results/student-case-expansion-runtime/builds',hash);fs.mkdirSync(build,{recursive:true});
  fs.writeFileSync(path.join(build,file),files[0]);fs.writeFileSync(path.join(build,driver),files[1]);
  let command,executable;
  if(config.runtime==='java') {
    env.LD_LIBRARY_PATH='/usr/lib/jvm/java-11-openjdk-amd64/lib/jli';
    executable=path.join(build,'Driver.class');
    command=[path.join(runtime,'usr/lib/jvm/java-11-openjdk-amd64/bin/javac'),'-d',build,path.join(build,file),path.join(build,driver)];
  } else {
    env.GOROOT=path.join(runtime,'usr/lib/go-1.13');env.GOCACHE=path.join(root,'results/student-case-expansion-runtime/go-cache');env.GO111MODULE='off';
    executable=path.join(build,'probe');command=[path.join(env.GOROOT,'bin/go'),'build','-o',executable,path.join(build,file),path.join(build,driver)];
  }
  if(!fs.existsSync(executable)) {
    const run=cp.spawnSync(command[0],command.slice(1),{env,encoding:'utf8',timeout:120000});
    fs.writeFileSync(path.join(build,'compile-receipt.json'),JSON.stringify({command,cwd:process.cwd(),exit_code:run.status,stdout:run.stdout,stderr:run.stderr},null,2));
    if(run.status!==0)throw new Error(run.stderr||String(run.error));
  }
  return {command:config.runtime==='java'?['java','-cp',build,'Driver']:[executable],env};
};
