import { collectMetrics } from "./metrics-consumer.js";
import { renderPresence } from "./presence-panel.js";

export async function render({ token, bootstrapMode }) {
  const [presence, metrics] = await Promise.all([
    renderPresence(token, bootstrapMode),
    collectMetrics(token),
  ]);
  return { presence, metrics };
}
