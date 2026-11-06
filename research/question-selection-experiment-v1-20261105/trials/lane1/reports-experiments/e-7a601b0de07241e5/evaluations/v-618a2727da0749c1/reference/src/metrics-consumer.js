import { observeChannel } from "./channel.js";

export function collectMetrics(token) {
  // Metrics deliberately attach after the synchronous bootstrap and count deltas only.
  return observeChannel({ token, bootstrapMode: "synchronous" });
}
