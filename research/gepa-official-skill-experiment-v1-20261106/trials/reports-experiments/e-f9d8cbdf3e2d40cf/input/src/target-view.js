import { runTarget } from "./temporal-flow.js";
export class TemporalView { constructor(){this.value="";} async run(input){const result=await runTarget(input);this.value=result.value;return result;} }

