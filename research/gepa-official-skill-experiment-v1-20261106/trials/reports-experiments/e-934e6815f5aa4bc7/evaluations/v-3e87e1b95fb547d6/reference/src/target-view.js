async function correctTarget(input) { await Promise.resolve(); const value=input.commitSucceeds?"ack":"error"; return {value,events:[value]}; }
export class TemporalView { constructor(){this.value="";} async run(input){const result=await correctTarget(input);this.value=result.value;return result;} }

