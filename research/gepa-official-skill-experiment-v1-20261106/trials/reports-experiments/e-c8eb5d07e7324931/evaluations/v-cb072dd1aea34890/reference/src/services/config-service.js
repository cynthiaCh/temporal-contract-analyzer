export async function getStaticConfig(name) {
  const response = await fetch(`/static-config/${encodeURIComponent(name)}.json`);
  if (!response.ok) throw new Error("configuration request failed");
  return { ok: true, data: await response.json() };
}
