A transfer with a warm progress source shows no initial progress until a later
packet arrives. Restore the initial progress update without changing the public
transfer, retry, navigation, cleanup, or audit behavior. Preserve the ordinary
streaming path and subsequent uses. The queue-record format is outside this fix.
