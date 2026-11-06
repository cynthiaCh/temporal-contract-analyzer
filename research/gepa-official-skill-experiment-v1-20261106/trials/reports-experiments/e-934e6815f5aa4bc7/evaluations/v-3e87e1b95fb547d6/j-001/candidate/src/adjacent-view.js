import { runAdjacent } from "./temporal-flow.js";
export class TemporalView { constructor(){this.value="";} async run(input){const result=await runAdjacent(input);this.value=result.value;return result;} }

