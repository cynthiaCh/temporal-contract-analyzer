// Synthetic demonstration, not an independently collected project incident.
function createPanel(fetchValue, publish) {
  let epoch = 0;
  async function refresh() {
    const value = await fetchValue();
    publish(value);
  }
  function close() {
    epoch += 1;
  }
  return {refresh, close};
}
module.exports = {createPanel};
