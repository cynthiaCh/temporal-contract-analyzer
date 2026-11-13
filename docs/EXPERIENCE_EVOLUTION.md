# Execution protocol

All new learning and testing uses [TempoEvo V4](TEMPOEVO_V4.md).
The V1–V3 orchestration engines and `experience-evolution` command are removed.
Historical batch JSON, reports, patches, scores and memory decisions are unchanged.
Use `history status --root BATCH` or `history report --root BATCH` to inspect them
without validating against current implementation hashes, writing reports, or
launching models. See [retirement boundaries](LEGACY_RETIREMENT.md).
