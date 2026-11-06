Fixed direct profile saving so it emits success only after the commit succeeds. A failed commit now produces only an error, so the page no longer receives a success acknowledgement that could trigger navigation. The adjacent acknowledgement flow was left unchanged.

Verified successful and failed saves, the failed-save view state, and the adjacent flow with a Node check; all passed.