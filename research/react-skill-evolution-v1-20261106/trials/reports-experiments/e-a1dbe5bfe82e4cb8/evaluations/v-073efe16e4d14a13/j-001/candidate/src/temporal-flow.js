"use strict";

async function runTarget(input) { let value="none"; await Promise.resolve(); if(input.loadedFlag)value="premium-action"; return {value,events:[value]}; }
async function runAdjacent(input) { const value=input.clickBeforeReady?"emergency-action":"none"; await Promise.resolve(); return {value,events:[value]}; }

module.exports = { runTarget, runAdjacent };

