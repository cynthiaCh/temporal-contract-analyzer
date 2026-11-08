async function runTarget(input){let envelope="metadata";if(input.uploadFirst){await Promise.resolve();envelope="metadata+file";}const submitted=envelope;if(!input.uploadFirst){await Promise.resolve();envelope="metadata+file";}return {value:submitted,events:[submitted]};} async function runAdjacent(){const submitted="metadata";await Promise.resolve();return {value:submitted,events:[submitted]};}

export { runTarget, runAdjacent };

