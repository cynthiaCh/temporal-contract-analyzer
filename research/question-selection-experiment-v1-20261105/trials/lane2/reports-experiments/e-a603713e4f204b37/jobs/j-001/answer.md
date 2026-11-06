The draft editor now saves the latest text once a 120 ms quiet interval passes. Later editing bursts still save, and closing or switching documents flushes pending text. Submitting flushes the accepted text before creating its receipt.

I verified burst timing, subsequent saves, close, submit, and navigation triggered by a save callback. The adjacent search preview was untouched.