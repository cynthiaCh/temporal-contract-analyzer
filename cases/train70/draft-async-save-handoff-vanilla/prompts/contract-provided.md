Additional contract: retire the old status owner before flushing its pending save.
Submit once before navigation returns, without awaiting acknowledgement. Recheck
navigation priority after the synchronous write-start callback. Associate status
with both visit and latest edit. Preserve store revision protection and every
accepted write; close does not revoke document-owned work.
