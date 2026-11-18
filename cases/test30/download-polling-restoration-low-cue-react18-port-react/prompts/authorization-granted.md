
Authorization update: migrate the background export panel to the dialog lifecycle as well. Closing either surface must stop its pending work and prevent any late status response from completing it.

