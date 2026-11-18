# Insurance tariff lookup

A shared per-key query cache provides subscribe(key,options) -> unique observer
handle, unsubscribe(handle), online(boolean), focus(boolean), snapshot(key),
and dispose() of observer scopes. Queries retain status (pending/success/error),
fetchStatus (idle/fetching/paused), and data. queryFn receives a lazy signal
accessor. Each actual access records consumption; each fetch owns its controller
and completion. Completion is asynchronous; initial online entry is synchronous,
paused continuation resumes on a Promise turn. First start uses network mode;
continuation also needs focus. 'always' can run offline; 'offlineFirst' allows
first offline entry but retry can pause. Retries use explicit scheduler handles.
Multiple observers share one fetch. Unconsumed active work can finish into cache
after its view departs; consumed work is physically abortable. Cancellation
reverts previous query data/status and settles the originating attempt. Late
fulfillment cannot become a new attempt's data. Unknown unsubscribe is inert.
The component owns observer scope; the cache remains outside individual views.
Dependency versions and build/test configuration are outside the repair scope.

Embedding API: bind registers a native callable; Environment.call
provides newAttempt(key,number), abort(key,number), request(key,number, lazy-read
token, completion token), defer(callback token), schedule(callback token,delay).
The request host calls queryFn with an actual AbortSignal property. Reading it
invokes the native consumption closure synchronously; Promise settlement later
invokes the native completion with {ok,value}. All observer, retry, cancellation,
state and cache logic executes in the target language. No native JS Promise or
DOM claim is made. Native object identity binds query and attempt generations;
wire handles only identify injected callbacks. 
PHP cache and observer objects; lazy context getter and Closure waiter
