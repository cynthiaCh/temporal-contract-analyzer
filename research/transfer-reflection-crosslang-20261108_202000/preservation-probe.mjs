// Supplemental training-only preservation witness; original official scoring is unchanged.
// Visible basis: README requires audit/public retry behavior retained; queue.receive
// uses current visit only, retry keeps that visit; source supports no cached packet.
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const root=process.argv[2];
const {createTransferWorkspace,createProgressFeed}=await import(pathToFileURL(path.join(root,'src/workspace.js')));
let settle;
const frame={loaded:7};
const feed=createProgressFeed({initialPacket:undefined,decode:()=>new Promise(resolve=>{settle=()=>resolve(frame);})});
const audit=[],visible=[],queue=[];
const file={id:'file',size:10,progressFeed:feed};
const w=createTransferWorkspace({transport:()=>{},onCancel:()=>{},record:e=>queue.push(e),showQueued:()=>{},recordProgress:e=>audit.push(e),showProgress:e=>visible.push(e)});
w.select(file);feed.emit({});w.retry();settle();await Promise.resolve();await Promise.resolve();
const result={scenario:'accepted old-attempt completion in same visit with no newer arrival/publication',audit,visible,queue,snapshot:w.snapshot()};
w.dispose();console.log(JSON.stringify(result));
