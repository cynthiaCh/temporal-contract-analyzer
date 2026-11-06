The Personnel editor now reads `src/config/personnel-form.json` locally. It waits for the form API before applying the config, preserving the parent-value write and picker behavior. The Structure editor is unchanged.

The JSON check passed, and a source check confirmed that only the Structure editor still calls the remote config service. No test script is provided in this workspace.