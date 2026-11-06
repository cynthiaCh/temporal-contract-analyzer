<template><output>{{ value }}</output></template>
<script>
const { ref } = require("vue");
async function correctTarget(input) { await Promise.resolve(); const value=input.loadedFlag?"premium-action":"none"; return {value,events:[value]}; }
export default { name: "TargetView", setup() { const value=ref(""); async function run(input){const result=await correctTarget(input);value.value=result.value;return result;} return {value,run}; } };
</script>

