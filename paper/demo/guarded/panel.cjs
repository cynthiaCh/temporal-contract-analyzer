// Synthetic demonstration: the reviewer supplies the epoch check.
function createPanel(fetchValue, publish) {
  let epoch = 0;
  async function refresh() {
    const started = epoch;
    const value = await fetchValue();
    if (started !== epoch) return;
    publish(value);
  }
  function close() {
    epoch += 1;
  }
  return {refresh, close};
}
module.exports = {createPanel};
