
Authorization update: migrate the background export panel to the dialog lifecycle as well. Closing either surface must stop its pending work and prevent any late status response from completing it.

The authorized background start uses dialog ownership too: it starts a new
generation, makes the panel visible, and invalidates earlier responses. Ready
delivery remains deduplicated for the artifact token. Final owner disposal still
retires all responses and retry timers.
