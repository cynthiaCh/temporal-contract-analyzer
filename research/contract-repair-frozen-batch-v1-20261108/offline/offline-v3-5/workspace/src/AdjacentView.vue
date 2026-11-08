<template><output>{{ value }}</output></template>
<script>
const { ref } = require("vue");
const { runAdjacent } = require("./temporal-flow.js");
export default { name: "AdjacentView", setup() { const value=ref(""); async function run(input){const result=await runAdjacent(input);value.value=result.value;return result;} return {value,run}; } };
</script>

