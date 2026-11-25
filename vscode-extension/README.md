# TempoEvo: My Experiences

A local VS Code editor for your own experience library. Browse, search, create,
edit and delete experiences. Save applies your changes directly; no reviewer,
approval or model call is required.

## Use

1. Install the VSIX and open a trusted workspace. Python 3.9+ is required on the
   extension host; configure **TempoEvo: Python Path** if automatic discovery fails.
2. In Explorer, open **My experiences** and choose **Choose experience library**.
   Select a categorized library directory, or an empty directory to start your
   own. The existing repository library is `experience-memory/library`.
3. Open the editor. Search and filter the list, select an experience, then edit
   its title, Abstract and guidance. Select applicable obligation labels and
   mechanisms from the existing taxonomy. At least one required mechanism is
   needed by the current retrieval format.
4. **Save** updates guidance and Abstract together for future library reads.
   Existing prepared experiments retain their snapshots. The Abstract is required
   because retrieval indexes it; keep it consistent with the guidance.
5. **History** loads a previous saved entry into the editor. Inspect it and press
   **Save** to restore it. Deleted entries can also be restored this way.

Before replacing or deleting an entry, its original record is backed up under
`LIBRARY/.history/`. External edits are detected when saving; reload before
retrying a conflicting edit. Navigating within the editor asks before discarding
unsaved changes. Save before closing the editor or VS Code.

Automatic suggestions remain separate from usable content until you explicitly
save them. An existing pending revision is indicated; saving replaces that
suggestion with your editor content. Historical evidence bindings are shown as
source information. An owner edit detaches the old proposal/evidence binding
because it no longer attests to the new guidance; the original remains in History.

The underlying library retains its existing acceptance fields for compatibility
with CLI consumers. Owner saves fill these internally, without an approval step.
The standalone research review workflow is unchanged. No source scanning starts
when this extension activates; the former scan commands are no longer contributed.

Choosing a library remembers it on this extension host and takes precedence over
`temporalContracts.experienceStore`. Remote development requires Python and the
library on the remote host. Browser-based VS Code is unsupported. No library,
source code or model credentials are uploaded or bundled into the extension.

## Development

The editor bundles Python modules and needs no JavaScript source parsers. Run:

```sh
cd vscode-extension
npm ci --ignore-scripts --no-audit --no-fund
npm run stage
npm test
npm run test:experiences
npm run package
```

`npm test` exercises the packaged Python experience bridge. `test:experiences` checks the owner
editor in Chrome with a simulated VS Code messaging bridge. Legacy scan-specific
`test:legacy`, host and browser suites apply to the former scanner, not the new entrypoint.
The Python owner-save tests live in `tests/test_owner_experience.py`.

The private VSIX is written under `../dist/`. No Marketplace publication or Git
commit is performed by packaging.
