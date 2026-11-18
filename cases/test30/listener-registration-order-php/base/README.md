# Hotel dispatch team availability

This workspace receives initial channel presence and subsequent updates. Sources may deliver during connection or after it. Channels can outlive a panel visit and be selected again. Host publication is an integration boundary that may synchronously navigate or hide. Decoding may complete immediately or later; removing reception does not retract an already-started decode. The metrics consumer deliberately excludes initial state. Public interfaces and payloads must remain compatible. Native host API spellings and dependencies are in docs/host-api.md.
