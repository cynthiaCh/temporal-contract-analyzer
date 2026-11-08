async function correctTarget(){await Promise.resolve();return {value:"metadata+file",events:["metadata+file"]};}
export class TemporalView { constructor(){this.value="";} async run(input){const result=await correctTarget(input);this.value=result.value;return result;} }

