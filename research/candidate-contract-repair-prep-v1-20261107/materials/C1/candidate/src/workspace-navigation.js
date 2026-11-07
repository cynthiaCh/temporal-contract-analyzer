import { createPresencePanel } from "./presence-panel.js";

// Presence publication can synchronously select a different room or hide the
// panel (for example, a room chooser reacting to an empty bootstrap snapshot).
// Reusing a transport object on a later visit is supported by the workspace.
export function createWorkspaceNavigation(renderState) {
  const panel = createPresencePanel((value) => renderState(value, navigation));
  const navigation = {
    select(channel, mode = "synchronous") { panel.show(channel, mode); },
    hide() { panel.close(); },
  };
  return navigation;
}
