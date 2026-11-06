Optimize only a reusable temporal-contract checking skill supplied to a code-maintenance agent. The original task, execution system, tools, retrieval, scoring and ending protocol are fixed and cannot be changed. This is reflection and instruction proposal, not a maintenance run: do not call tools, read files, run commands or ask questions. Everything needed for this proposal is in this message.

Current skill:
```
# Temporal contract skill: ownership, completion, and effects

Purpose: complete the original maintenance task. Use this skill to inspect timing and ownership where they matter. The original task and visible project evidence define the required behavior.

S1 Applicability. Check whether work can finish after its initiating access, operation, or consumer changes; whether callbacks can reenter during setup, cleanup, scheduling, or publication; or whether one result feeds effects with different validity rules. If none applies, briefly record why and continue the maintenance task.

S2 Establish evidence. Read the entry point, actual producer or decoder, completion path, ownership transitions, cancellation path, and every affected consumer. Inspect adjacent implementations only for supported patterns, not as automatic specifications. Record source locations for consequential facts. Separate explicit requirements, observed source behavior, hypotheses, and unavailable evidence. A function name, familiar framework pattern, or passing self-written check does not establish a contract.

S3 Name the identities and effects. Where the source distinguishes them, track the resource, access or visit, physical operation or attempt, and accepted result. For each effect—such as history, current display, delivery, notification, or scheduled work—state which identity must still be valid when the effect occurs. Determine whether cancellation prevents new input, stops scheduled callbacks, aborts running work, or merely releases a consumer. Do not apply a single stale-result guard to every effect without evidence.

S4 Trace the whole handoff. Follow the order in which listeners are attached, work starts, handles become available, ownership is published, and cleanup runs. At every call into external or user code, consider synchronous reentry. Check the state both before and after such calls when later steps depend on the original owner. If cleanup can trigger another access, ensure the old operation cannot subsequently publish ownership or an effect over the new one. If startup can produce an immediate result, verify that its intended consumers are ready and that its history and current effects follow their respective contracts.

S5 Compare concrete event orders. Using APIs visible in the project, exercise ordinary completion; completion after close, switch, or disposal; reuse of the same resource under a new access; replacement or retry within an access; and synchronous callback reentry where supported. When results may settle out of order, compare normal and reversed completion order. Derive ordering from source-supported identity or arrival sequence; do not invent a payload schema. Observe each effect separately, including effects of superseded work that the contract still retains. For scheduled retries or polling, compare pending-to-ready behavior with close, reopen, replacement, unmount, and a callback that runs during scheduling when the API permits it.

S6 Preserve established behavior. Keep public interfaces, unrelated consumers of shared helpers, ordinary streaming, records, diagnostics, cleanup, and adjacent behavior consistent with the task. Distinguish an access ending from an attempt ending: the same resource may be reused, and a retry may keep the access while replacing its operation. Do not infer that closing a view cancels a background obligation, or that a stored effect must disappear with a visible one. Resolve these questions from source and task evidence; otherwise mark them unknown.

S7 Repair and verify. Implement the smallest supported change that completes the original maintenance task. Run relevant available checks and inspect their actual output. Add focused checks only for meaningful untested orders, including at least one boundary or reentry path when applicable; assert the separate effects and ownership state, not merely that code ran. A local harness establishes only the paths it drives. Treat unavailable dependencies, failed commands, syntax checks, and unrun behavior checks according to what they actually prove. If a check fails, revise the repair and rerun the relevant check. Finish with the maintenance result and explicit remaining uncertainty; a contract discussion alone is not completion.
```

Actual train executions and grounded feedback:
```
# Example 1
## Inputs
### original_maintenance_task
# Task

The preparation service can now report that a file is still pending before it becomes ready. Update the file download dialog so it keeps checking pending preparation and delivers the file only after a ready status.

### visible_context
# Retrieved candidate context

Raw source, configuration and documentation excerpts selected using the original task only. Retrieval is incomplete; inspect other candidate files when needed.

## package.json:1-10
```
{
  "name": "download-polling-restoration-low-cue-react18-fixture",
  "version": "0.0.0",
  "private": true,
  "dependencies": {
    "react": "18.3.1",
    "react-dom": "18.3.1"
  }
}
```

## src/BackgroundExportPanel.jsx:1-48
```
"use strict";

const React = require("react");
const api = require("./preparation-api.js");

class BackgroundExportPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = { visible: true, loading: false, retryScheduled: false, checkCount: 0, completed: [], token: props.token };
    this.retry = null;
    this.active = true;
  }

  componentWillUnmount() {
    this.active = false;
    if (this.retry !== null) api.cancelPreparationRetry(this.retry);
  }

  start = () => {
    const token = this.state.token;
    this.setState((state) => ({ loading: true, checkCount: state.checkCount + 1 }));
    api.checkPreparation(token).then((done) => {
      if (!this.active) return;
      if (done) {
        this.retry = null;
        this.setState((state) => ({
          loading: false,
          retryScheduled: false,
          completed: state.completed.includes(token) ? state.completed : [...state.completed, token],
        }));
      } else {
        this.retry = api.schedulePreparationRetry(this.start);
        this.setState({ retryScheduled: true });
      }
    });
  };

  close = () => this.setState({ visible: false });

  snapshot = () => ({ ...this.state, completed: [...this.state.completed] });

  render() {
    return React.createElement("section", {
      "data-surface": "background-export",
      "data-visible": String(this.state.visible),
      "data-loading": String(this.state.loading),
    });
  }
```

## src/DownloadDialog.jsx:1-18
```
"use strict";

const React = require("react");
const { usePreparation } = require("./usePreparation.js");

const DownloadDialog = React.forwardRef(function DownloadDialog({ token }, ref) {
  const preparation = usePreparation(token);
  React.useImperativeHandle(ref, () => preparation);
  const snapshot = preparation.snapshot();
  return React.createElement("section", {
    "data-surface": "download-dialog",
    "data-visible": String(snapshot.visible),
    "data-loading": String(snapshot.loading),
  });
});

module.exports = { DownloadDialog };
```

## src/preparation-api.js:1-27
```
"use strict";

function checkPreparation(token) {
  if (typeof globalThis.__preparationTransport !== "function") {
    throw new Error("preparation transport is not installed");
  }
  return globalThis.__preparationTransport(token);
}

function schedulePreparationRetry(callback) {
  if (typeof globalThis.__schedulePreparationRetry !== "function") {
    throw new Error("retry scheduler is not installed");
  }
  return globalThis.__schedulePreparationRetry(callback);
}

function cancelPreparationRetry(handle) {
  if (typeof globalThis.__cancelPreparationRetry === "function") {
    globalThis.__cancelPreparationRetry(handle);
  }
}

module.exports = {
  checkPreparation,
  schedulePreparationRetry,
  cancelPreparationRetry,
};
```

## src/usePreparation.js:1-48
```
"use strict";

const React = require("react");
const { checkPreparation } = require("./preparation-api.js");

function usePreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => render();
  const check = () => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      state.current.loading = false;
      if (status) state.current.completed.push(requestToken);
      publish();
    });
  };

  return {
    start: check,
    close() {
      state.current.visible = false;
      publish();
    },
    reopen(nextToken) {
      state.current.token = nextToken;
      state.current.visible = true;
      publish();
      check();
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
```

## Generated_Outputs
### actual_reads
#### Item 1
##### event_line
9

##### command
/usr/bin/bash -lc 'cat src/usePreparation.js src/BackgroundExportPanel.jsx src/DownloadDialog.jsx package.json'

##### candidate_paths
###### Item 1
package.json

###### Item 2
src/BackgroundExportPanel.jsx

###### Item 3
src/DownloadDialog.jsx

###### Item 4
src/usePreparation.js

### modified_locations
#### Item 1
##### path
src/usePreparation.js

##### diff
--- before/src/usePreparation.js
+++ after/src/usePreparation.js
@@ -1,7 +1,7 @@
 "use strict";
 
 const React = require("react");
-const { checkPreparation } = require("./preparation-api.js");
+const { checkPreparation, schedulePreparationRetry, cancelPreparationRetry } = require("./preparation-api.js");
 
 function usePreparation(initialToken) {
   const state = React.useRef({
@@ -13,31 +13,77 @@
     token: initialToken,
   });
   const [, render] = React.useReducer((value) => value + 1, 0);
+  const lifecycle = React.useRef({ generation: 0, retry: null, mounted: true });
+
+  React.useEffect(() => {
+    lifecycle.current.mounted = true;
+    return () => {
+      lifecycle.current.mounted = false;
+      lifecycle.current.generation += 1;
+      if (lifecycle.current.retry !== null) cancelPreparationRetry(lifecycle.current.retry);
+      lifecycle.current.retry = null;
+    };
+  }, []);
 
   const publish = () => render();
-  const check = () => {
+  const cancelRetry = () => {
+    if (lifecycle.current.retry !== null) cancelPreparationRetry(lifecycle.current.retry);
+    lifecycle.current.retry = null;
+    state.current.retryScheduled = false;
+  };
+  const check = (generation) => {
     const requestToken = state.current.token;
     state.current.loading = true;
     state.current.checkCount += 1;
     publish();
     checkPreparation(requestToken).then((status) => {
+      if (!lifecycle.current.mounted || lifecycle.current.generation !== generation) return;
       state.current.loading = false;
-      if (status) state.current.completed.push(requestToken);
-      publish();
+      if (status) {
+        if (!state.current.completed.includes(requestToken)) state.current.completed.push(requestToken);
+        state.current.retryScheduled = false;
+        publish();
+      } else {
+        let fired = false;
+        const retry = schedulePreparationRetry(() => {
+          fired = true;
+          if (!lifecycle.current.mounted || lifecycle.current.generation !== generation) return;
+          lifecycle.current.retry = null;
+          state.current.retryScheduled = false;
+          check(generation);
+        });
+        if (lifecycle.current.mounted && lifecycle.current.generation === generation && !fired) {
+          lifecycle.current.retry = retry;
+          state.current.retryScheduled = true;
+          publish();
+        } else {
+          cancelPreparationRetry(retry);
+        }
+      }
     });
   };
 
+  const start = () => {
+    lifecycle.current.generation += 1;
+    cancelRetry();
+    check(lifecycle.current.generation);
+  };
+
   return {
-    start: check,
+    start,
     close() {
+      lifecycle.current.generation += 1;
+      cancelRetry();
       state.current.visible = false;
+      state.current.loading = false;
       publish();
     },
     reopen(nextToken) {
+      lifecycle.current.generation += 1;
+      cancelRetry();
       state.current.token = nextToken;
       state.current.visible = true;
-      publish();
-      check();
+      check(lifecycle.current.generation);
     },
     snapshot() {
       return { ...state.current, completed: [...state.current.completed] };

##### truncated
False

### tool_observations
#### Item 1
##### event_line
7

##### command
/usr/bin/bash -lc "rg --files -g '"'!node_modules'"' -g '"'!package-lock.json'"'"

##### exit_code
0

##### actual_output
package.json
src/preparation-api.js
src/DownloadDialog.jsx
src/usePreparation.js
src/BackgroundExportPanel.jsx

##### output_truncated
False

##### command_truncated
False

#### Item 2
##### event_line
9

##### command
/usr/bin/bash -lc 'cat src/usePreparation.js src/BackgroundExportPanel.jsx src/DownloadDialog.jsx package.json'

##### exit_code
0

##### actual_output
"use strict";

const React = require("react");
const { checkPreparation } = require("./preparation-api.js");

function usePreparation(initialToken) {
  const state = React.useRef({
    visible: true,
    loading: false,
    retryScheduled: false,
    checkCount: 0,
    completed: [],
    token: initialToken,
  });
  const [, render] = React.useReducer((value) => value + 1, 0);

  const publish = () => render();
  const check = () => {
    const requestToken = state.current.token;
    state.current.loading = true;
    state.current.checkCount += 1;
    publish();
    checkPreparation(requestToken).then((status) => {
      state.current.loading = false;
      if (status) state.current.completed.push(requestToken);
      publish();
    });
  };

  return {
    start: check,
    close() {
      state.current.visible = false;
      publish();
    },
    reopen(nextToken) {
      state.current.token = nextToken;
      state.current.visible = true;
      publish();
      check();
    },
    snapshot() {
      return { ...state.current, completed: [...state.current.completed] };
    },
  };
}

module.exports = { usePreparation };
"use strict";

const React = require("react");
const api = require("./preparation-api.js");

class BackgroundExportPanel extends React.Component {
  constructor(props) {
    super(props);
    this.state = { visible: true, loading: false, retryScheduled: false, checkCount: 0, completed: [], token: props.token };
    this.retry = null;
    this.active = true;
  }

  componentWillUnmount() {
    this.active = false;
    if (this.retry !== null) api.cancelPreparationRetry(this.retry);
  }

  start = () => {
    const token = this.state.token;
    this.setState((state) => ({ loading: true, checkCount: state.checkCount + 1 }));
    api.checkPreparation(token).then((done) => {
      if (!this.active) return;
      if (done) {
        this.retry = null;
        this.setState((state) => ({
          loading: false,
          retryScheduled: false,
          completed: state.completed.includes(token) ? state.completed : [...state.completed, token],
        }));
      } else {
        this.retry = api.schedulePreparationRetry(this.start);
        this.setState({ retryScheduled: true });
      }
    });
  };

  close = () => this.setState({ visible: false });

  snapshot = () => ({ ...this.state, completed: [...this.state.completed] });

  render() {
    return React.createElement("section", {
      "data-surface": "background-export",
      "data-visible": String(this.state.visible),
      "data-loading": String(this.state.loading),
    });
  }
}

module.exports = { BackgroundExportPanel };
"use strict";

const React = require("react");
const { usePreparation } = require("./usePreparation.js");

const DownloadDialog = React.forwardRef(function DownloadDialog({ token }, ref) {
  const preparation = usePreparation(token);
  React.useImperativeHandle(ref, () => preparation);
  const snapshot = preparation.snapshot();
  return React.createElement("section", {
    "data-surface": "download-dialog",
    "data-visible": String(snapshot.visible),
    "data-loading": String(snapshot.loading),
  });
});

module.exports = { DownloadDialog };

{
  "name": "download-polling-restoration-low-cue-react18-fixture",
  "version": "0.0.0",
  "private": true,
  "dependencies": {
    "react": "18.3.1",
    "react-dom": "18.3.1"
  }
}

##### output_truncated
False

##### command_truncated
False

#### Item 3
##### event_line
14

##### command
/usr/bin/bash -lc 'git diff -- src/usePreparation.js'

##### exit_code
129

##### actual_output
warning: Not a git repository. Use --no-index to compare two paths outside a working tree
usage: git diff --no-index [<options>] <path> <path>

Diff output format options
    -p, --patch           generate patch
    -s, --no-patch        suppress diff output
    -u                    generate patch
    -U, --unified[=<n>]   generate diffs with <n> lines context
    -W, --function-context
                          generate diffs with <n> lines context
    --raw                 generate the diff in raw format
    --patch-with-raw      synonym for '-p --raw'
    --patch-with-stat     synonym for '-p --stat'
    --numstat             machine friendly --stat
    --shortstat           output only the last line of --stat
    -X, --dirstat[=<param1,param2>...]
                          output the distribution of relative amount of changes for each sub-directory
    --cumulative          synonym for --dirstat=cumulative
    --dirstat-by-file[=<param1,param2>...]
                          synonym for --dirstat=files,param1,param2...
    --check               warn if changes introduce conflict markers or whitespace errors
    --summary             condensed summary such as creations, renames and mode changes
    --name-only           show only names of changed files
    --name-status         show only names and status of changed files
    --stat[=<width>[,<name-width>[,<count>]]]
                          generate diffstat
    --stat-width <width>  generate diffstat with a given width
    --stat-name-width <width>
                          generate diffstat with a given name width
    --stat-graph-width <width>
                          generate diffstat with a given graph width
    --stat-count <count>  generate diffstat with limited lines
    --compact-summary     generate compact summary in diffstat
    --binary              output a binary diff that can be applied
    --full-index          show full pre- and post-image object names on the "index" lines
    --color[=<when>]      show colored diff
    --ws-error-highlight <kind>
                          highlight whitespace errors in the 'context', 'old' or 'new' lines in the diff
    -z                    do not munge pathnames and use NULs as output field terminators in --raw or --numstat
    --abbrev[=<n>]        use <n> digits to display SHA-1s
    --src-prefix <prefix>
                          show the given source prefix instead of "a/"
    --dst-prefix <prefix>
                          show the given destination prefix instead of "b/"
    --line-prefix <prefix>
                          prepend an additional prefix to every line of output
    --no-prefix           do not show any source or destination prefix
    --inter-hunk-context <n>
                          show context between diff hunks up to the specified number of lines
    --output-indicator-new <char>
                          specify the character to indicate a new line instead of '+'
    --output-indicator-old <char>
                          specify the character to indicate an old line instead of '-'
    --output-indicator-context <char>
                          specify the character to indicate a context instead of ' '

Diff rename options
    -B, --break-rewrites[=<n>[/<m>]]
                          break complete rewrite changes into pairs of delete and create
    -M, --find-renames[=<n>]
                          detect renames
    -D, --irreversible-delete
                          omit the preimage for deletes
    -C, --find-copies[=<n>]
                          detect copies
    --find-copies-harder  use unmodified files as source to find copies
    --no-renames          disable rename detection
    --rename-empty        use empty blobs as rename source
    --follow              continue listing the history of a file beyond renames
    -l <n>                prevent rename/copy detection if the number of rename/copy targets exceeds given limit

Diff algorithm options
    --minimal             produce the smallest possible diff
    -w, --ignore-all-space
                          ignore whitespace when comparing lines
    -b, --ignore-space-change
                          ignore changes in amount of whitespace
    --ignore-space-at-eol
                          ignore changes in whitespace at EOL
    --ignore-cr-at-eol    ignore carrier-return at the end of line
    --ignore-blank-lines  ignore changes whose lines are all blank
    --indent-heuristic    heuristic to shift diff hunk boundaries for easy reading
    --patience            generate diff using the "patience diff" algorithm
    --histogram           generate diff using the "histogram diff" algorithm
    --diff-algorithm <algorithm>
                          choose a diff algorithm
    --anchored <text>     generate diff using the "anchored diff" algorithm
    --word-diff[=<mode>]  show word diff, using <mode> to delimit changed words
    --word-diff-regex <regex>
                          use <regex> to decide what a word

##### output_truncated
True

##### command_truncated
False

#### Item 4
##### event_line
16

##### command
/usr/bin/bash -lc 'test -d node_modules && echo installed || echo missing'

##### exit_code
0

##### actual_output
missing

##### output_truncated
False

##### command_truncated
False

#### Item 5
##### event_line
18

##### command
/usr/bin/bash -lc 'node --check src/usePreparation.js'

##### exit_code
0

##### actual_output


##### output_truncated
False

##### command_truncated
False

### visible_validation
#### Item 1
##### event_line
18

##### command
/usr/bin/bash -lc 'node --check src/usePreparation.js'

##### exit_code
0

##### actual_output


##### output_truncated
False

##### command_truncated
False

### delivery
#### candidate_patch_present
True

#### trustworthy_whole_task_pass
False

#### execution_category
behavior

## Feedback
