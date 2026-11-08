// A downstream consumer: archived submissions are value snapshots, not live
// references to a draft. capture/list never invoke application integrations.
export function createReceiptArchive() {
  const receipts = [];
  return {
    capture({ id, text }) {
      const receipt = Object.freeze({ id, text });
      receipts.push(receipt);
      return receipt;
    },
    list() { return receipts.map(receipt => ({ ...receipt })); },
  };
}
