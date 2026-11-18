'use strict';
const candidate=process.env.FTC_NATIVE_CANDIDATE;
let bridge;
globalThis[Symbol.for('native-buffer-host')]=()=>{
 if(!bridge){const launch=require('./native-launch.cjs').launch(candidate,__dirname);bridge=require('./bridge.cjs')(launch.command,{env:launch.env});if(process.env.FTC_NATIVE_EXECUTION_LOG){const fs=require('fs'),crypto=require('crypto'),file={java:'Workflow.java',python3:'workflow.py',php:'workflow.php',ruby:'workflow.rb',go:'workflow.go'}[require('./adapter.json').runtime];fs.writeFileSync(process.env.FTC_NATIVE_EXECUTION_LOG,JSON.stringify({command:launch.command,cwd:process.cwd(),started_at:new Date().toISOString(),native_source_sha256:crypto.createHash('sha256').update(fs.readFileSync(require('path').join(candidate,'src',file))).digest('hex'),host_node:process.version}));}}
 return bridge.createController({},{});
};
process.on('exit',()=>{if(bridge)bridge.finish();});
