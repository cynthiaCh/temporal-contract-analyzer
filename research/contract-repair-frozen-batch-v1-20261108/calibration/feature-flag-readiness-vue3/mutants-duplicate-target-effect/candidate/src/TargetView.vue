<template><output>{{ value }}</output></template>
<script>
const { ref } = require("vue");
async function baseCorrectTarget(input) { await Promise.resolve(); const value=input.loadedFlag?"premium-action":"none"; return {value,events:[value]}; }
async function correctTarget(input){const result=await baseCorrectTarget(input);return {value:result.value,events:[result.value,result.value]};}
export default { name: "TargetView", setup() { const value=ref(""); async function run(input){const result=await correctTarget(input);value.value=result.value;return result;} return {value,run}; } };
</script>

