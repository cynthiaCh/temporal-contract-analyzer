<template><output>{{ value }}</output></template>
<script>
const { ref } = require("vue");
const { runTarget } = require("./temporal-flow.js");
export default { name: "TargetView", setup() { const value=ref(""); async function run(input){const result=await runTarget(input);value.value=result.value;return result;} return {value,run}; } };
</script>

