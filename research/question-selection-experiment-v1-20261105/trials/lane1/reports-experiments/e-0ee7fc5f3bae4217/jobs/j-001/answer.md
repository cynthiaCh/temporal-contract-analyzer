The draft editor now saves the latest text after a 120 ms quiet interval. Later editing bursts still save. Closing or switching documents flushes pending text, and submitting persists the accepted snapshot before creating its receipt.

I verified burst coalescing, later bursts, close and switch behavior, and navigation during a save callback. The search preview was untouched.