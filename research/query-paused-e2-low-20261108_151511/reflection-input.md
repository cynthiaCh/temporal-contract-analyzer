根据已冻结经验E1及后续同题对照的源绑定成功与失败证据，只做一次Reflection，修订为唯一候选E2。训练是经验文本更新，不是权重训练，不进行搜索或第二轮改写。
经验须写明适用机制与前提、应查证的事件关系、验证动作、必须保留的相邻行为、不适用情况。
不得写入案例ID、评分/测试断言名称或专用值、文件名/API/字段名、可直接复制的代码补丁。使用事件、身份、归属和生命周期关系表达；不要把观察猜测升级为新政策。只输出经验正文。
返回JSON唯一字段report，最多6000个Unicode字符。不要调用工具。

本轮修订关注：在保留三项目标改善的同时，区分单次尝试有效性/取消控制器与共享查询状态的生命周期。依据源码与标准解释应查证什么、验证什么；不要直接给出补丁，不把本例字段名或评分项写入通用经验。

E1原文：
适用于共享缓存、观察者与请求尝试生命周期分离，且请求可因网络/焦点条件暂停并在条件恢复后异步续行的机制。修复“卸载后恢复触发”类问题时，应先按尝试身份区分：尚未真正进入请求执行的初始暂停尝试、已启动但未消费取消能力的后台工作、已消费取消能力的活动工作，以及带既有缓存结果的刷新尝试；不能只按“当前无观察者”一概处理。

应查证的事件关系是：订阅创建尝试、条件不足使其暂停、最后一个观察者离开、网络或焦点恢复、恢复回调入队与实际执行之间的再次卸载，以及随后重新订阅。尤其要确认“是否曾进入执行”与“是否读取取消能力”分别何时记录，尝试是否仍属于当前代际，以及暂停尝试在被弃用时是否已终结并恢复空闲活动状态。

验证应覆盖：初始暂停尝试在无人观察时不会因恢复条件而首次执行或暴露有效取消能力；其生命周期状态不会遗留为暂停；恢复已入队后再卸载也不会穿透检查；重新订阅仍能按既有规则恢复；有缓存结果的未消费后台刷新仍可保留、恢复、完成并更新缓存；已启动但未消费的工作仍可在视图离开后完成；已消费的工作仍按取消、回滚和代际隔离规则处理。还应检查多观察者共享、网络模式、焦点门控、重试续行和晚到完成的原有行为。

必须保留相邻行为：缓存不等同于视图生命周期；未消费的已启动后台工作可具有独立于观察者的合法寿命；消费取消能力后才具备物理取消语义；取消须结算来源尝试并恢复其先前状态；旧代际完成不得写入新代际；恢复条件、首次启动条件和重试条件应继续按各自既有规则判定。

不适用于没有共享缓存或异步恢复队列的简单请求模型，也不应据此推出“无观察者即取消全部工作”或“任何暂停尝试都可无限保留”。对于是否保留某个无人观察的暂停尝试，需依据它是否已启动、是否承载既有缓存刷新及原有生命周期约定判断；若这些约定未被证实，应保持未知而非扩展为新政策。

原任务：
Repair the transit stop lookup cache: a fresh online-mode query mounted and unmounted entirely offline later calls its signal-consuming query function with a live signal after reconnect. This occurs independently of refetchOnReconnect. Preserve supported query behavior, interfaces, dependencies and build/test configuration. Change product source only.


候选可见文档与源码：
SOURCE README.md
# Transit stop lookup

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
Module cache and EventTarget subscription handles; actual Node16 promises


SOURCE src/session.js
class Attempt {
 constructor(number,state,options){this.number=number;this.previous={...state};this.options=options;this.controller=new AbortController();this.settled=false;this.consumed=false;this.retryCancelled=false;this.failures=0;this.queued=false;}
}
export class Session {
 constructor(host,initial={}){this.host=host;this.cache=new Map();this.handles=new Map();this.connected=initial.online!==false;this.focused=initial.focused!==false;this.serial=0;this.fetchSerial=0;this.project=()=>{};}
 eligible(a){return this.focused&&((a.options.networkMode||'online')==='always'||this.connected);}
 active(q,a){return q.attempt===a&&!a.settled;}
 cancel(q,a){if(a.settled)return;a.settled=true;q.state={...a.previous,fetchStatus:'idle'};a.controller.abort();this.project(q);}
 invoke(q,a){a.queued=false;if(!this.active(q,a))return;q.state.fetchStatus='fetching';q.consumed=false;const context={key:q.key,attempt:a.number};Object.defineProperty(context,'signal',{enumerable:true,get(){q.consumed=true;return a.controller.signal;}});let value;try{value=this.host.queryFn(context);}catch(e){value=Promise.reject(e);}Promise.resolve(value).then(value=>{if(!this.active(q,a))return;a.settled=true;q.state={...q.state,data:value,status:'success',fetchStatus:'idle'};this.project(q);},()=>{if(!this.active(q,a))return;if(!a.retryCancelled&&a.failures<(a.options.retry||0)){a.failures++;this.host.timers.schedule(()=>{if(!this.active(q,a))return;if(a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}else if(this.eligible(a))this.invoke(q,a);else q.state.fetchStatus='paused';this.project(q);},a.options.retryDelay||10);}else{a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}this.project(q);});this.project(q);}
 resume(q){const a=q.attempt;if(a&&this.active(q,a)&&q.state.fetchStatus==='paused'&&this.eligible(a)&&!a.queued){a.queued=true;Promise.resolve().then(()=>{a.queued=false;if(!this.active(q,a))return;if(a.failures&&a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};this.project(q);return;}this.invoke(q,a);});}}
 subscribe(key,options={}){let q=this.cache.get(key);if(!q){const data=options.initialData===undefined?null:options.initialData;q={key,state:{status:data===null?'pending':'success',fetchStatus:'idle',data},observers:new Set(),attempt:null,consumed:false};this.cache.set(key,q);}const handle=++this.serial;this.handles.set(handle,q);q.observers.add(handle);if(q.attempt&&!q.attempt.settled){q.attempt.retryCancelled=false;this.resume(q);}else{const a=new Attempt(++this.fetchSerial,q.state,options);q.attempt=a;if((options.networkMode||'online')!=='online'||this.connected)this.invoke(q,a);else q.state.fetchStatus='paused';}this.project(q);return handle;}
 unsubscribe(handle){const q=this.handles.get(handle);if(!q)return;this.handles.delete(handle);q.observers.delete(handle);if(q.observers.size===0){const a=q.attempt;if(a&&!a.settled){if(q.consumed)this.cancel(q,a);else a.retryCancelled=true;}}this.project(q);}
 online(value){this.connected=value;for(const q of this.cache.values())this.resume(q);}
 focus(value){this.focused=value;for(const q of this.cache.values())this.resume(q);}
 snapshot(key){return {...this.cache.get(key).state};}
 dispose(){for(const handle of [...this.handles.keys()])this.unsubscribe(handle);}
}


本轮成功与失败的真实反馈及标准依据：
{
  "projection": "AI-assisted offline source/trace/score evidence; not another model judgment",
  "source_batch": "/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-paused-frozen-experience-followup-20261108_144036",
  "E1_instruction_assessment": {
    "explicit_attempt_consumption_migration_required": false,
    "actual_emphasis": [
      "按尝试身份区分",
      "是否曾进入执行与是否读取取消能力分别何时记录",
      "依据是否已启动、缓存刷新及原有生命周期约定判断"
    ],
    "omitted_boundary": "No explicit reset/ownership rule separating shared consumption state from attempt/controller validity.",
    "causality_limit": "Potential overextension is a hypothesis. Visible plans and patches establish chosen implementation, not hidden reasoning or single-sentence causation."
  },
  "source_behavior": {
    "actual_entry": "invoke resets query-level consumption; lazy getter marks its owning query and returns originating attempt controller",
    "paused_creation": "subscribe constructs new attempt without resetting existing query consumption",
    "last_observer": "unsubscribe consults query-level consumption before canceling originating current attempt",
    "ownership_boundary": "Shared query state and individual attempt/controller identity have different lifetimes; their existing contracts must be established separately."
  },
  "standard": {
    "obligation": {
      "id": "lazy-signal-consumption",
      "statement": "Signal getter marks query-level consumption lazily; reset occurs only at actual queryFn entry. Paused attempts retain prior consumption and last-observer cancellation policy.",
      "event_relation": "Signal getter marks query-level consumption lazily; reset occurs only at actual queryFn entry. Paused attempts retain prior consumption and last-observer cancellation policy.",
      "failure_if_violated": "Signal getter marks query-level consumption lazily; reset occurs only at actual queryFn entry. Paused attempts retain prior consumption and last-observer cancellation policy.",
      "acceptable_evidence_paths": [
        "base/README.md",
        "base/src/session.js"
      ],
      "required_concepts": [
        "Signal getter marks query-level consumption lazily; reset occurs only at actual queryFn entry. Paused attempts retain prior consumption and last-observer cancellation policy."
      ]
    },
    "assertion_witnesses": [
      {
        "schedule": "offline-nonconsuming-detach",
        "assertion_id": "no-background-initial-pending",
        "relationships": [
          "initial-paused-retirement"
        ],
        "observable_actual": 0,
        "expected": 0,
        "reference_passed": true
      },
      {
        "schedule": "offline-nonconsuming-detach",
        "assertion_id": "idle-after-cancel",
        "relationships": [
          "initial-paused-retirement"
        ],
        "observable_actual": "idle",
        "expected": "idle",
        "reference_passed": true
      },
      {
        "schedule": "cached-paused-background",
        "assertion_id": "cached-pause-status",
        "relationships": [
          "preserved-background-work"
        ],
        "observable_actual": {
          "status": "success",
          "fetchStatus": "paused",
          "data": "retained"
        },
        "expected": {
          "status": "success",
          "fetchStatus": "paused",
          "data": "retained"
        },
        "reference_passed": true
      },
      {
        "schedule": "cached-paused-background",
        "assertion_id": "cached-unconsumed-work-preserved",
        "relationships": [
          "preserved-background-work"
        ],
        "observable_actual": 1,
        "expected": 1,
        "reference_passed": true
      },
      {
        "schedule": "cached-paused-background",
        "assertion_id": "cached-refresh-success",
        "relationships": [
          "preserved-background-work"
        ],
        "observable_actual": "refresh",
        "expected": "refresh",
        "reference_passed": true
      },
      {
        "schedule": "cached-later-consumption",
        "assertion_id": "cached-later-signal-read-allowed",
        "relationships": [
          "lazy-signal-consumption"
        ],
        "observable_actual": 1,
        "expected": 1,
        "reference_passed": true
      },
      {
        "schedule": "cached-later-consumption",
        "assertion_id": "cached-later-live-entry",
        "relationships": [
          "attempt-settlement"
        ],
        "observable_actual": false,
        "expected": false,
        "reference_passed": true
      },
      {
        "schedule": "cached-later-consumption",
        "assertion_id": "cached-later-result",
        "relationships": [
          "attempt-settlement"
        ],
        "observable_actual": "refresh",
        "expected": "refresh",
        "reference_passed": true
      },
      {
        "schedule": "cached-prior-consumed-success",
        "assertion_id": "prior-consumed-new-attempt-paused",
        "relationships": [
          "initial-paused-retirement"
        ],
        "observable_actual": "paused",
        "expected": "paused",
        "reference_passed": true
      },
      {
        "schedule": "cached-prior-consumed-success",
        "assertion_id": "prior-consumption-not-cleared-by-paused-attempt",
        "relationships": [
          "lazy-signal-consumption"
        ],
        "observable_actual": 1,
        "expected": 1,
        "reference_passed": true
      },
      {
        "schedule": "cached-prior-consumed-success",
        "assertion_id": "prior-data-preserved",
        "relationships": [
          "attempt-settlement"
        ],
        "observable_actual": "retained",
        "expected": "retained",
        "reference_passed": true
      },
      {
        "schedule": "retained-context-query-flag",
        "assertion_id": "old-context-marks-owning-query-flag",
        "relationships": [
          "lazy-signal-consumption"
        ],
        "observable_actual": 1,
        "expected": 1,
        "reference_passed": true
      },
      {
        "schedule": "retained-context-query-flag",
        "assertion_id": "retained-context-controller-independent",
        "relationships": [
          "lazy-signal-consumption"
        ],
        "observable_actual": false,
        "expected": false,
        "reference_passed": true
      },
      {
        "schedule": "retained-context-query-flag",
        "assertion_id": "retained-context-cache-preserved",
        "relationships": [
          "lazy-signal-consumption"
        ],
        "observable_actual": "retained",
        "expected": "retained",
        "reference_passed": true
      }
    ],
    "original_source_sha256": "6460e5caedd3bc5c87d2f968736b18961f4234724897908d08e65b3ac36b9700",
    "standard_worker_sha256": "64453b6ab372b66d620fbab2d4eb6c862869c166e6369f5755c4cc59ec6914da"
  },
  "runs": [
    {
      "slot": "block-1-B",
      "effects": {
        "offline-detach-false": true,
        "offline-detach-true": true,
        "offline-detach-always": true,
        "offline-nonconsuming-detach": true,
        "active-offline-resume": true,
        "multiple-observers": true,
        "last-observer-offline": true,
        "unknown-unsubscribe": true,
        "consumed-flight-cancel": true,
        "nonconsuming-flight-cache": true,
        "cached-paused-background": true,
        "cached-consumed-revert": true,
        "remount-generation": true,
        "late-old-generation": true,
        "always-mode": true,
        "focus-gates-resume": true,
        "focus-does-not-gate-first-start": true,
        "offline-first-retry": true,
        "nonconsuming-cancel-retry": true,
        "reentrant-unsubscribe-at-entry": true,
        "framework-unmount": true,
        "cached-later-consumption": true,
        "accepted-resume-then-offline": true,
        "detach-after-resume-queued": true,
        "independent-query-keys": true,
        "cached-prior-consumed-success": false,
        "cached-prior-consumed-cancelled": true,
        "retained-context-query-flag": false,
        "dependency-config-preserved": true
      },
      "verdict": "UNDERREACH",
      "positive_targets": [
        "cached-later-consumption",
        "cached-paused-background",
        "offline-nonconsuming-detach"
      ],
      "failures": [
        "cached-prior-consumed-success",
        "retained-context-query-flag"
      ],
      "relevant_raw_schedules": {
        "cached-later-consumption": {
          "scenario": "cached-later-consumption",
          "passed": true,
          "runtimeError": null,
          "checks": [
            {
              "id": "cached-later-signal-read-allowed",
              "actual": 1,
              "expected": 1,
              "passed": true
            },
            {
              "id": "cached-later-live-entry",
              "actual": false,
              "expected": false,
              "passed": true
            },
            {
              "id": "cached-later-result",
              "actual": "refresh",
              "expected": "refresh",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": false,
              "abortedAfter": false
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "refresh"
          }
        },
        "cached-paused-background": {
          "scenario": "cached-paused-background",
          "passed": true,
          "runtimeError": null,
          "checks": [
            {
              "id": "cached-pause-status",
              "actual": {
                "status": "success",
                "fetchStatus": "paused",
                "data": "retained"
              },
              "expected": {
                "status": "success",
                "fetchStatus": "paused",
                "data": "retained"
              },
              "passed": true
            },
            {
              "id": "cached-unconsumed-work-preserved",
              "actual": 1,
              "expected": 1,
              "passed": true
            },
            {
              "id": "cached-refresh-success",
              "actual": "refresh",
              "expected": "refresh",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": null,
              "abortedAfter": null
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "refresh"
          }
        },
        "offline-nonconsuming-detach": {
          "scenario": "offline-nonconsuming-detach",
          "passed": true,
          "runtimeError": null,
          "checks": [
            {
              "id": "no-background-initial-pending",
              "actual": 0,
              "expected": 0,
              "passed": true
            },
            {
              "id": "idle-after-cancel",
              "actual": "idle",
              "expected": "idle",
              "passed": true
            }
          ],
          "calls": [],
          "state": {
            "status": "pending",
            "fetchStatus": "idle",
            "data": null
          }
        },
        "cached-prior-consumed-success": {
          "scenario": "cached-prior-consumed-success",
          "passed": false,
          "runtimeError": null,
          "checks": [
            {
              "id": "prior-consumed-new-attempt-paused",
              "actual": "paused",
              "expected": "paused",
              "passed": true
            },
            {
              "id": "prior-consumption-not-cleared-by-paused-attempt",
              "actual": 2,
              "expected": 1,
              "passed": false
            },
            {
              "id": "prior-data-preserved",
              "actual": "retained",
              "expected": "retained",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": false,
              "abortedAfter": false
            },
            {
              "key": "K",
              "attempt": 2,
              "abortedAtInvocation": false,
              "abortedAfter": false
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "cleanup"
          }
        },
        "retained-context-query-flag": {
          "scenario": "retained-context-query-flag",
          "passed": false,
          "runtimeError": null,
          "checks": [
            {
              "id": "old-context-marks-owning-query-flag",
              "actual": 2,
              "expected": 1,
              "passed": false
            },
            {
              "id": "retained-context-controller-independent",
              "actual": false,
              "expected": false,
              "passed": true
            },
            {
              "id": "retained-context-cache-preserved",
              "actual": "retained",
              "expected": "retained",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": null,
              "abortedAfter": null
            },
            {
              "key": "K",
              "attempt": 2,
              "abortedAtInvocation": null,
              "abortedAfter": null
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "cleanup"
          }
        }
      },
      "consumption_change": "attempt only",
      "explicit_model_plan": {
        "event_line": 24,
        "text": "{\"report\":\"已修复 src/session.js：为每次请求尝试记录是否已实际进入执行及是否消费 signal。无人观察时，从未执行且无缓存结果的初始暂停尝试会被终结并恢复为 pending/idle，重连或已入队恢复均无法再调用 queryFn；重新订阅会正常创建新尝试。已启动未消费请求、已消费取消、共享观察者及带缓存的后台刷新维持原有行为。\\n\\n验证：/runtime/node --version 为 v16.20.2；通过语法检查及内联断言，覆盖离线卸载后重连、恢复入队后卸载、重新订阅、未消费工作完成写缓存、缓存刷新恢复、signal 取消和多观察者共享。未安装依赖；项目未提供测试脚本。\"}"
      },
      "actual_patch": "--- a/src/session.js\n+++ b/src/session.js\n@@ -1,15 +1,15 @@\n class Attempt {\n- constructor(number,state,options){this.number=number;this.previous={...state};this.options=options;this.controller=new AbortController();this.settled=false;this.consumed=false;this.retryCancelled=false;this.failures=0;this.queued=false;}\n+ constructor(number,state,options){this.number=number;this.previous={...state};this.options=options;this.controller=new AbortController();this.settled=false;this.started=false;this.consumed=false;this.retryCancelled=false;this.failures=0;this.queued=false;}\n }\n export class Session {\n  constructor(host,initial={}){this.host=host;this.cache=new Map();this.handles=new Map();this.connected=initial.online!==false;this.focused=initial.focused!==false;this.serial=0;this.fetchSerial=0;this.project=()=>{};}\n  eligible(a){return this.focused&&((a.options.networkMode||'online')==='always'||this.connected);}\n  active(q,a){return q.attempt===a&&!a.settled;}\n  cancel(q,a){if(a.settled)return;a.settled=true;q.state={...a.previous,fetchStatus:'idle'};a.controller.abort();this.project(q);}\n- invoke(q,a){a.queued=false;if(!this.active(q,a))return;q.state.fetchStatus='fetching';q.consumed=false;const context={key:q.key,attempt:a.number};Object.defineProperty(context,'signal',{enumerable:true,get(){q.consumed=true;return a.controller.signal;}});let value;try{value=this.host.queryFn(context);}catch(e){value=Promise.reject(e);}Promise.resolve(value).then(value=>{if(!this.active(q,a))return;a.settled=true;q.state={...q.state,data:value,status:'success',fetchStatus:'idle'};this.project(q);},()=>{if(!this.active(q,a))return;if(!a.retryCancelled&&a.failures<(a.options.retry||0)){a.failures++;this.host.timers.schedule(()=>{if(!this.active(q,a))return;if(a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}else if(this.eligible(a))this.invoke(q,a);else q.state.fetchStatus='paused';this.project(q);},a.options.retryDelay||10);}else{a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}this.project(q);});this.project(q);}\n+ invoke(q,a){a.queued=false;if(!this.active(q,a))return;a.started=true;q.state.fetchStatus='fetching';const context={key:q.key,attempt:a.number};Object.defineProperty(context,'signal',{enumerable:true,get(){a.consumed=true;return a.controller.signal;}});let value;try{value=this.host.queryFn(context);}catch(e){value=Promise.reject(e);}Promise.resolve(value).then(value=>{if(!this.active(q,a))return;a.settled=true;q.state={...q.state,data:value,status:'success',fetchStatus:'idle'};this.project(q);},()=>{if(!this.active(q,a))return;if(!a.retryCancelled&&a.failures<(a.options.retry||0)){a.failures++;this.host.timers.schedule(()=>{if(!this.active(q,a))return;if(a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}else if(this.eligible(a))this.invoke(q,a);else q.state.fetchStatus='paused';this.project(q);},a.options.retryDelay||10);}else{a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}this.project(q);});this.project(q);}\n  resume(q){const a=q.attempt;if(a&&this.active(q,a)&&q.state.fetchStatus==='paused'&&this.eligible(a)&&!a.queued){a.queued=true;Promise.resolve().then(()=>{a.queued=false;if(!this.active(q,a))return;if(a.failures&&a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};this.project(q);return;}this.invoke(q,a);});}}\n- subscribe(key,options={}){let q=this.cache.get(key);if(!q){const data=options.initialData===undefined?null:options.initialData;q={key,state:{status:data===null?'pending':'success',fetchStatus:'idle',data},observers:new Set(),attempt:null,consumed:false};this.cache.set(key,q);}const handle=++this.serial;this.handles.set(handle,q);q.observers.add(handle);if(q.attempt&&!q.attempt.settled){q.attempt.retryCancelled=false;this.resume(q);}else{const a=new Attempt(++this.fetchSerial,q.state,options);q.attempt=a;if((options.networkMode||'online')!=='online'||this.connected)this.invoke(q,a);else q.state.fetchStatus='paused';}this.project(q);return handle;}\n- unsubscribe(handle){const q=this.handles.get(handle);if(!q)return;this.handles.delete(handle);q.observers.delete(handle);if(q.observers.size===0){const a=q.attempt;if(a&&!a.settled){if(q.consumed)this.cancel(q,a);else a.retryCancelled=true;}}this.project(q);}\n+ subscribe(key,options={}){let q=this.cache.get(key);if(!q){const data=options.initialData===undefined?null:options.initialData;q={key,state:{status:data===null?'pending':'success',fetchStatus:'idle',data},observers:new Set(),attempt:null};this.cache.set(key,q);}const handle=++this.serial;this.handles.set(handle,q);q.observers.add(handle);if(q.attempt&&!q.attempt.settled){q.attempt.retryCancelled=false;this.resume(q);}else{const a=new Attempt(++this.fetchSerial,q.state,options);q.attempt=a;if((options.networkMode||'online')!=='online'||this.connected)this.invoke(q,a);else q.state.fetchStatus='paused';}this.project(q);return handle;}\n+ unsubscribe(handle){const q=this.handles.get(handle);if(!q)return;this.handles.delete(handle);q.observers.delete(handle);if(q.observers.size===0){const a=q.attempt;if(a&&!a.settled){if(!a.started&&a.previous.status==='pending'){a.settled=true;q.state={...a.previous,fetchStatus:'idle'};}else if(a.consumed)this.cancel(q,a);else a.retryCancelled=true;}}this.project(q);}\n  online(value){this.connected=value;for(const q of this.cache.values())this.resume(q);}\n  focus(value){this.focused=value;for(const q of this.cache.values())this.resume(q);}\n  snapshot(key){return {...this.cache.get(key).state};}\n",
      "actual_final_report": "{\"report\":\"已修复 src/session.js：为每次请求尝试记录是否已实际进入执行及是否消费 signal。无人观察时，从未执行且无缓存结果的初始暂停尝试会被终结并恢复为 pending/idle，重连或已入队恢复均无法再调用 queryFn；重新订阅会正常创建新尝试。已启动未消费请求、已消费取消、共享观察者及带缓存的后台刷新维持原有行为。\\n\\n验证：/runtime/node --version 为 v16.20.2；通过语法检查及内联断言，覆盖离线卸载后重连、恢复入队后卸载、重新订阅、未消费工作完成写缓存、缓存刷新恢复、signal 取消和多观察者共享。未安装依赖；项目未提供测试脚本。\"}",
      "visible_messages": [
        {
          "event_line": 5,
          "text": "{\"report\":\"我会只检查 /workspace 的产品源码与现有测试，先定位查询缓存的暂停/恢复生命周期，再做最小修复并用 /runtime/node 记录版本和运行相关验证。\"}"
        },
        {
          "event_line": 10,
          "text": "{\"report\":\"定位到根因：离线初始请求只标记为 paused；最后一个观察者离开时它被标为可取消重试，却仍保持活动。重连的恢复队列只检查“活动”，因此会首次调用 queryFn。将为“从未进入执行且无缓存结果”的初始暂停尝试显式终结；已启动的未消费请求和带缓存的刷新保持现有寿命。\"}"
        },
        {
          "event_line": 17,
          "text": "{\"report\":\"核心回归与恢复队列竞态已通过：离线初始请求在重连前后都不会启动；重新订阅会创建并执行新尝试；已启动未消费请求仍可在卸载后写入缓存；已有缓存的离线刷新仍会在重连后完成。接着补一轮语法和相邻取消/共享观察者检查。\"}"
        },
        {
          "event_line": 24,
          "text": "{\"report\":\"已修复 src/session.js：为每次请求尝试记录是否已实际进入执行及是否消费 signal。无人观察时，从未执行且无缓存结果的初始暂停尝试会被终结并恢复为 pending/idle，重连或已入队恢复均无法再调用 queryFn；重新订阅会正常创建新尝试。已启动未消费请求、已消费取消、共享观察者及带缓存的后台刷新维持原有行为。\\n\\n验证：/runtime/node --version 为 v16.20.2；通过语法检查及内联断言，覆盖离线卸载后重连、恢复入队后卸载、重新订阅、未消费工作完成写缓存、缓存刷新恢复、signal 取消和多观察者共享。未安装依赖；项目未提供测试脚本。\"}"
        }
      ],
      "source": "/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-paused-frozen-experience-followup-20261108_144036/runs/block-1-B/archive"
    },
    {
      "slot": "block-2-B",
      "effects": {
        "offline-detach-false": true,
        "offline-detach-true": true,
        "offline-detach-always": true,
        "offline-nonconsuming-detach": true,
        "active-offline-resume": true,
        "multiple-observers": true,
        "last-observer-offline": true,
        "unknown-unsubscribe": true,
        "consumed-flight-cancel": true,
        "nonconsuming-flight-cache": true,
        "cached-paused-background": true,
        "cached-consumed-revert": true,
        "remount-generation": true,
        "late-old-generation": true,
        "always-mode": true,
        "focus-gates-resume": true,
        "focus-does-not-gate-first-start": true,
        "offline-first-retry": true,
        "nonconsuming-cancel-retry": true,
        "reentrant-unsubscribe-at-entry": true,
        "framework-unmount": true,
        "cached-later-consumption": true,
        "accepted-resume-then-offline": true,
        "detach-after-resume-queued": true,
        "independent-query-keys": true,
        "cached-prior-consumed-success": false,
        "cached-prior-consumed-cancelled": true,
        "retained-context-query-flag": false,
        "dependency-config-preserved": true
      },
      "verdict": "UNDERREACH",
      "positive_targets": [
        "cached-later-consumption",
        "cached-paused-background",
        "offline-nonconsuming-detach"
      ],
      "failures": [
        "cached-prior-consumed-success",
        "retained-context-query-flag"
      ],
      "relevant_raw_schedules": {
        "cached-later-consumption": {
          "scenario": "cached-later-consumption",
          "passed": true,
          "runtimeError": null,
          "checks": [
            {
              "id": "cached-later-signal-read-allowed",
              "actual": 1,
              "expected": 1,
              "passed": true
            },
            {
              "id": "cached-later-live-entry",
              "actual": false,
              "expected": false,
              "passed": true
            },
            {
              "id": "cached-later-result",
              "actual": "refresh",
              "expected": "refresh",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": false,
              "abortedAfter": false
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "refresh"
          }
        },
        "cached-paused-background": {
          "scenario": "cached-paused-background",
          "passed": true,
          "runtimeError": null,
          "checks": [
            {
              "id": "cached-pause-status",
              "actual": {
                "status": "success",
                "fetchStatus": "paused",
                "data": "retained"
              },
              "expected": {
                "status": "success",
                "fetchStatus": "paused",
                "data": "retained"
              },
              "passed": true
            },
            {
              "id": "cached-unconsumed-work-preserved",
              "actual": 1,
              "expected": 1,
              "passed": true
            },
            {
              "id": "cached-refresh-success",
              "actual": "refresh",
              "expected": "refresh",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": null,
              "abortedAfter": null
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "refresh"
          }
        },
        "offline-nonconsuming-detach": {
          "scenario": "offline-nonconsuming-detach",
          "passed": true,
          "runtimeError": null,
          "checks": [
            {
              "id": "no-background-initial-pending",
              "actual": 0,
              "expected": 0,
              "passed": true
            },
            {
              "id": "idle-after-cancel",
              "actual": "idle",
              "expected": "idle",
              "passed": true
            }
          ],
          "calls": [],
          "state": {
            "status": "pending",
            "fetchStatus": "idle",
            "data": null
          }
        },
        "cached-prior-consumed-success": {
          "scenario": "cached-prior-consumed-success",
          "passed": false,
          "runtimeError": null,
          "checks": [
            {
              "id": "prior-consumed-new-attempt-paused",
              "actual": "paused",
              "expected": "paused",
              "passed": true
            },
            {
              "id": "prior-consumption-not-cleared-by-paused-attempt",
              "actual": 2,
              "expected": 1,
              "passed": false
            },
            {
              "id": "prior-data-preserved",
              "actual": "retained",
              "expected": "retained",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": false,
              "abortedAfter": false
            },
            {
              "key": "K",
              "attempt": 2,
              "abortedAtInvocation": false,
              "abortedAfter": false
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "cleanup"
          }
        },
        "retained-context-query-flag": {
          "scenario": "retained-context-query-flag",
          "passed": false,
          "runtimeError": null,
          "checks": [
            {
              "id": "old-context-marks-owning-query-flag",
              "actual": 2,
              "expected": 1,
              "passed": false
            },
            {
              "id": "retained-context-controller-independent",
              "actual": false,
              "expected": false,
              "passed": true
            },
            {
              "id": "retained-context-cache-preserved",
              "actual": "retained",
              "expected": "retained",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": null,
              "abortedAfter": null
            },
            {
              "key": "K",
              "attempt": 2,
              "abortedAtInvocation": null,
              "abortedAfter": null
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "cleanup"
          }
        }
      },
      "consumption_change": "writes attempt and query; cancellation reads attempt only",
      "explicit_model_plan": {
        "event_line": 10,
        "text": "{\"report\":\"已确认根因：离线首次订阅留下的 `paused` 尝试在最后一个观察者离开后只被标记为“取消重试”，却仍保持活动；重连的续行队列因而首次执行了它。我将仅终结“从未执行、无缓存初始状态”的该类尝试，并把取消能力消费记录绑定到尝试本身。\"}"
      },
      "actual_patch": "--- a/src/session.js\n+++ b/src/session.js\n@@ -6,10 +6,10 @@\n  eligible(a){return this.focused&&((a.options.networkMode||'online')==='always'||this.connected);}\n  active(q,a){return q.attempt===a&&!a.settled;}\n  cancel(q,a){if(a.settled)return;a.settled=true;q.state={...a.previous,fetchStatus:'idle'};a.controller.abort();this.project(q);}\n- invoke(q,a){a.queued=false;if(!this.active(q,a))return;q.state.fetchStatus='fetching';q.consumed=false;const context={key:q.key,attempt:a.number};Object.defineProperty(context,'signal',{enumerable:true,get(){q.consumed=true;return a.controller.signal;}});let value;try{value=this.host.queryFn(context);}catch(e){value=Promise.reject(e);}Promise.resolve(value).then(value=>{if(!this.active(q,a))return;a.settled=true;q.state={...q.state,data:value,status:'success',fetchStatus:'idle'};this.project(q);},()=>{if(!this.active(q,a))return;if(!a.retryCancelled&&a.failures<(a.options.retry||0)){a.failures++;this.host.timers.schedule(()=>{if(!this.active(q,a))return;if(a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}else if(this.eligible(a))this.invoke(q,a);else q.state.fetchStatus='paused';this.project(q);},a.options.retryDelay||10);}else{a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}this.project(q);});this.project(q);}\n+ invoke(q,a){a.queued=false;if(!this.active(q,a))return;a.started=true;q.state.fetchStatus='fetching';q.consumed=false;const context={key:q.key,attempt:a.number};Object.defineProperty(context,'signal',{enumerable:true,get(){a.consumed=true;q.consumed=true;return a.controller.signal;}});let value;try{value=this.host.queryFn(context);}catch(e){value=Promise.reject(e);}Promise.resolve(value).then(value=>{if(!this.active(q,a))return;a.settled=true;q.state={...q.state,data:value,status:'success',fetchStatus:'idle'};this.project(q);},()=>{if(!this.active(q,a))return;if(!a.retryCancelled&&a.failures<(a.options.retry||0)){a.failures++;this.host.timers.schedule(()=>{if(!this.active(q,a))return;if(a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}else if(this.eligible(a))this.invoke(q,a);else q.state.fetchStatus='paused';this.project(q);},a.options.retryDelay||10);}else{a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}this.project(q);});this.project(q);}\n  resume(q){const a=q.attempt;if(a&&this.active(q,a)&&q.state.fetchStatus==='paused'&&this.eligible(a)&&!a.queued){a.queued=true;Promise.resolve().then(()=>{a.queued=false;if(!this.active(q,a))return;if(a.failures&&a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};this.project(q);return;}this.invoke(q,a);});}}\n  subscribe(key,options={}){let q=this.cache.get(key);if(!q){const data=options.initialData===undefined?null:options.initialData;q={key,state:{status:data===null?'pending':'success',fetchStatus:'idle',data},observers:new Set(),attempt:null,consumed:false};this.cache.set(key,q);}const handle=++this.serial;this.handles.set(handle,q);q.observers.add(handle);if(q.attempt&&!q.attempt.settled){q.attempt.retryCancelled=false;this.resume(q);}else{const a=new Attempt(++this.fetchSerial,q.state,options);q.attempt=a;if((options.networkMode||'online')!=='online'||this.connected)this.invoke(q,a);else q.state.fetchStatus='paused';}this.project(q);return handle;}\n- unsubscribe(handle){const q=this.handles.get(handle);if(!q)return;this.handles.delete(handle);q.observers.delete(handle);if(q.observers.size===0){const a=q.attempt;if(a&&!a.settled){if(q.consumed)this.cancel(q,a);else a.retryCancelled=true;}}this.project(q);}\n+ unsubscribe(handle){const q=this.handles.get(handle);if(!q)return;this.handles.delete(handle);q.observers.delete(handle);if(q.observers.size===0){const a=q.attempt;if(a&&!a.settled){if(a.consumed)this.cancel(q,a);else if(!a.started&&a.previous.status==='pending')this.cancel(q,a);else a.retryCancelled=true;}}this.project(q);}\n  online(value){this.connected=value;for(const q of this.cache.values())this.resume(q);}\n  focus(value){this.focused=value;for(const q of this.cache.values())this.resume(q);}\n  snapshot(key){return {...this.cache.get(key).state};}\n",
      "actual_final_report": "{\"report\":\"已修复 `src/session.js`：为尝试记录是否真正启动，并将 signal 消费绑定到该尝试。最后一个观察者离开时，尚未启动且无缓存初始状态的暂停尝试会结算为 idle，阻止重连（包括已入队的恢复回调）首次调用 queryFn；已启动的未消费工作及带缓存的刷新仍保留原有生命周期。\\n\\n验证：`/runtime/node --version` → v16.20.2；`/runtime/node --check src/session.js` 通过。运行内联断言覆盖离线首次卸载后重连不调用、恢复入队后再卸载不穿透、重新订阅、缓存刷新、未消费工作完成、已消费工作取消和多观察者共享，均通过。未安装依赖或修改构建/测试配置。\"}",
      "visible_messages": [
        {
          "event_line": 5,
          "text": "{\"report\":\"我会先定位查询缓存与网络恢复逻辑，仅读取产品源码和现有测试；随后做最小修复并用指定 Node 运行相关验证。\"}"
        },
        {
          "event_line": 10,
          "text": "{\"report\":\"已确认根因：离线首次订阅留下的 `paused` 尝试在最后一个观察者离开后只被标记为“取消重试”，却仍保持活动；重连的续行队列因而首次执行了它。我将仅终结“从未执行、无缓存初始状态”的该类尝试，并把取消能力消费记录绑定到尝试本身。\"}"
        },
        {
          "event_line": 15,
          "text": "{\"report\":\"修复已落在产品源码 `src/session.js`。首轮生命周期断言已通过；仓库不是 Git 工作树，因此无法使用 Git 的差异检查，我会改用 Node 语法检查和覆盖“恢复已入队后卸载”的直接断言完成验证。\"}"
        },
        {
          "event_line": 18,
          "text": "{\"report\":\"已修复 `src/session.js`：为尝试记录是否真正启动，并将 signal 消费绑定到该尝试。最后一个观察者离开时，尚未启动且无缓存初始状态的暂停尝试会结算为 idle，阻止重连（包括已入队的恢复回调）首次调用 queryFn；已启动的未消费工作及带缓存的刷新仍保留原有生命周期。\\n\\n验证：`/runtime/node --version` → v16.20.2；`/runtime/node --check src/session.js` 通过。运行内联断言覆盖离线首次卸载后重连不调用、恢复入队后再卸载不穿透、重新订阅、缓存刷新、未消费工作完成、已消费工作取消和多观察者共享，均通过。未安装依赖或修改构建/测试配置。\"}"
        }
      ],
      "source": "/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-paused-frozen-experience-followup-20261108_144036/runs/block-2-B/archive"
    },
    {
      "slot": "block-3-B",
      "effects": {
        "offline-detach-false": true,
        "offline-detach-true": true,
        "offline-detach-always": true,
        "offline-nonconsuming-detach": true,
        "active-offline-resume": true,
        "multiple-observers": true,
        "last-observer-offline": true,
        "unknown-unsubscribe": true,
        "consumed-flight-cancel": true,
        "nonconsuming-flight-cache": true,
        "cached-paused-background": true,
        "cached-consumed-revert": true,
        "remount-generation": true,
        "late-old-generation": true,
        "always-mode": true,
        "focus-gates-resume": true,
        "focus-does-not-gate-first-start": true,
        "offline-first-retry": true,
        "nonconsuming-cancel-retry": true,
        "reentrant-unsubscribe-at-entry": true,
        "framework-unmount": true,
        "cached-later-consumption": true,
        "accepted-resume-then-offline": true,
        "detach-after-resume-queued": true,
        "independent-query-keys": true,
        "cached-prior-consumed-success": false,
        "cached-prior-consumed-cancelled": true,
        "retained-context-query-flag": false,
        "dependency-config-preserved": true
      },
      "verdict": "UNDERREACH",
      "positive_targets": [
        "cached-later-consumption",
        "cached-paused-background",
        "offline-nonconsuming-detach"
      ],
      "failures": [
        "cached-prior-consumed-success",
        "retained-context-query-flag"
      ],
      "relevant_raw_schedules": {
        "cached-later-consumption": {
          "scenario": "cached-later-consumption",
          "passed": true,
          "runtimeError": null,
          "checks": [
            {
              "id": "cached-later-signal-read-allowed",
              "actual": 1,
              "expected": 1,
              "passed": true
            },
            {
              "id": "cached-later-live-entry",
              "actual": false,
              "expected": false,
              "passed": true
            },
            {
              "id": "cached-later-result",
              "actual": "refresh",
              "expected": "refresh",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": false,
              "abortedAfter": false
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "refresh"
          }
        },
        "cached-paused-background": {
          "scenario": "cached-paused-background",
          "passed": true,
          "runtimeError": null,
          "checks": [
            {
              "id": "cached-pause-status",
              "actual": {
                "status": "success",
                "fetchStatus": "paused",
                "data": "retained"
              },
              "expected": {
                "status": "success",
                "fetchStatus": "paused",
                "data": "retained"
              },
              "passed": true
            },
            {
              "id": "cached-unconsumed-work-preserved",
              "actual": 1,
              "expected": 1,
              "passed": true
            },
            {
              "id": "cached-refresh-success",
              "actual": "refresh",
              "expected": "refresh",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": null,
              "abortedAfter": null
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "refresh"
          }
        },
        "offline-nonconsuming-detach": {
          "scenario": "offline-nonconsuming-detach",
          "passed": true,
          "runtimeError": null,
          "checks": [
            {
              "id": "no-background-initial-pending",
              "actual": 0,
              "expected": 0,
              "passed": true
            },
            {
              "id": "idle-after-cancel",
              "actual": "idle",
              "expected": "idle",
              "passed": true
            }
          ],
          "calls": [],
          "state": {
            "status": "pending",
            "fetchStatus": "idle",
            "data": null
          }
        },
        "cached-prior-consumed-success": {
          "scenario": "cached-prior-consumed-success",
          "passed": false,
          "runtimeError": null,
          "checks": [
            {
              "id": "prior-consumed-new-attempt-paused",
              "actual": "paused",
              "expected": "paused",
              "passed": true
            },
            {
              "id": "prior-consumption-not-cleared-by-paused-attempt",
              "actual": 2,
              "expected": 1,
              "passed": false
            },
            {
              "id": "prior-data-preserved",
              "actual": "retained",
              "expected": "retained",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": false,
              "abortedAfter": false
            },
            {
              "key": "K",
              "attempt": 2,
              "abortedAtInvocation": false,
              "abortedAfter": false
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "cleanup"
          }
        },
        "retained-context-query-flag": {
          "scenario": "retained-context-query-flag",
          "passed": false,
          "runtimeError": null,
          "checks": [
            {
              "id": "old-context-marks-owning-query-flag",
              "actual": 2,
              "expected": 1,
              "passed": false
            },
            {
              "id": "retained-context-controller-independent",
              "actual": false,
              "expected": false,
              "passed": true
            },
            {
              "id": "retained-context-cache-preserved",
              "actual": "retained",
              "expected": "retained",
              "passed": true
            }
          ],
          "calls": [
            {
              "key": "K",
              "attempt": 1,
              "abortedAtInvocation": null,
              "abortedAfter": null
            },
            {
              "key": "K",
              "attempt": 2,
              "abortedAtInvocation": null,
              "abortedAfter": null
            }
          ],
          "state": {
            "status": "success",
            "fetchStatus": "idle",
            "data": "cleanup"
          }
        }
      },
      "consumption_change": "attempt only",
      "explicit_model_plan": {
        "event_line": 10,
        "text": "{\"report\":\"已定位根因：离线创建的暂停尝试未区分“尚未执行”与“已执行但未读取 signal”，重连恢复路径因此会直接首次调用 queryFn。将把取消能力与是否实际启动记录到尝试级别，并仅终结无人观察的全新、未启动初始暂停尝试。\"}"
      },
      "actual_patch": "--- a/src/session.js\n+++ b/src/session.js\n@@ -1,15 +1,15 @@\n class Attempt {\n- constructor(number,state,options){this.number=number;this.previous={...state};this.options=options;this.controller=new AbortController();this.settled=false;this.consumed=false;this.retryCancelled=false;this.failures=0;this.queued=false;}\n+ constructor(number,state,options){this.number=number;this.previous={...state};this.options=options;this.controller=new AbortController();this.settled=false;this.started=false;this.consumed=false;this.retryCancelled=false;this.failures=0;this.queued=false;}\n }\n export class Session {\n  constructor(host,initial={}){this.host=host;this.cache=new Map();this.handles=new Map();this.connected=initial.online!==false;this.focused=initial.focused!==false;this.serial=0;this.fetchSerial=0;this.project=()=>{};}\n  eligible(a){return this.focused&&((a.options.networkMode||'online')==='always'||this.connected);}\n  active(q,a){return q.attempt===a&&!a.settled;}\n  cancel(q,a){if(a.settled)return;a.settled=true;q.state={...a.previous,fetchStatus:'idle'};a.controller.abort();this.project(q);}\n- invoke(q,a){a.queued=false;if(!this.active(q,a))return;q.state.fetchStatus='fetching';q.consumed=false;const context={key:q.key,attempt:a.number};Object.defineProperty(context,'signal',{enumerable:true,get(){q.consumed=true;return a.controller.signal;}});let value;try{value=this.host.queryFn(context);}catch(e){value=Promise.reject(e);}Promise.resolve(value).then(value=>{if(!this.active(q,a))return;a.settled=true;q.state={...q.state,data:value,status:'success',fetchStatus:'idle'};this.project(q);},()=>{if(!this.active(q,a))return;if(!a.retryCancelled&&a.failures<(a.options.retry||0)){a.failures++;this.host.timers.schedule(()=>{if(!this.active(q,a))return;if(a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}else if(this.eligible(a))this.invoke(q,a);else q.state.fetchStatus='paused';this.project(q);},a.options.retryDelay||10);}else{a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}this.project(q);});this.project(q);}\n+ invoke(q,a){a.queued=false;if(!this.active(q,a))return;a.started=true;q.state.fetchStatus='fetching';const context={key:q.key,attempt:a.number};Object.defineProperty(context,'signal',{enumerable:true,get(){a.consumed=true;return a.controller.signal;}});let value;try{value=this.host.queryFn(context);}catch(e){value=Promise.reject(e);}Promise.resolve(value).then(value=>{if(!this.active(q,a))return;a.settled=true;q.state={...q.state,data:value,status:'success',fetchStatus:'idle'};this.project(q);},()=>{if(!this.active(q,a))return;if(!a.retryCancelled&&a.failures<(a.options.retry||0)){a.failures++;this.host.timers.schedule(()=>{if(!this.active(q,a))return;if(a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}else if(this.eligible(a))this.invoke(q,a);else q.state.fetchStatus='paused';this.project(q);},a.options.retryDelay||10);}else{a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}this.project(q);});this.project(q);}\n  resume(q){const a=q.attempt;if(a&&this.active(q,a)&&q.state.fetchStatus==='paused'&&this.eligible(a)&&!a.queued){a.queued=true;Promise.resolve().then(()=>{a.queued=false;if(!this.active(q,a))return;if(a.failures&&a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};this.project(q);return;}this.invoke(q,a);});}}\n- subscribe(key,options={}){let q=this.cache.get(key);if(!q){const data=options.initialData===undefined?null:options.initialData;q={key,state:{status:data===null?'pending':'success',fetchStatus:'idle',data},observers:new Set(),attempt:null,consumed:false};this.cache.set(key,q);}const handle=++this.serial;this.handles.set(handle,q);q.observers.add(handle);if(q.attempt&&!q.attempt.settled){q.attempt.retryCancelled=false;this.resume(q);}else{const a=new Attempt(++this.fetchSerial,q.state,options);q.attempt=a;if((options.networkMode||'online')!=='online'||this.connected)this.invoke(q,a);else q.state.fetchStatus='paused';}this.project(q);return handle;}\n- unsubscribe(handle){const q=this.handles.get(handle);if(!q)return;this.handles.delete(handle);q.observers.delete(handle);if(q.observers.size===0){const a=q.attempt;if(a&&!a.settled){if(q.consumed)this.cancel(q,a);else a.retryCancelled=true;}}this.project(q);}\n+ subscribe(key,options={}){let q=this.cache.get(key);if(!q){const data=options.initialData===undefined?null:options.initialData;q={key,state:{status:data===null?'pending':'success',fetchStatus:'idle',data},observers:new Set(),attempt:null};this.cache.set(key,q);}const handle=++this.serial;this.handles.set(handle,q);q.observers.add(handle);if(q.attempt&&!q.attempt.settled){q.attempt.retryCancelled=false;this.resume(q);}else{const a=new Attempt(++this.fetchSerial,q.state,options);q.attempt=a;if((options.networkMode||'online')!=='online'||this.connected)this.invoke(q,a);else q.state.fetchStatus='paused';}this.project(q);return handle;}\n+ unsubscribe(handle){const q=this.handles.get(handle);if(!q)return;this.handles.delete(handle);q.observers.delete(handle);if(q.observers.size===0){const a=q.attempt;if(a&&!a.settled){if(!a.started&&a.previous.status==='pending'&&a.previous.data===null){a.settled=true;q.state={...a.previous,fetchStatus:'idle'};}else if(a.consumed)this.cancel(q,a);else a.retryCancelled=true;}}this.project(q);}\n  online(value){this.connected=value;for(const q of this.cache.values())this.resume(q);}\n  focus(value){this.focused=value;for(const q of this.cache.values())this.resume(q);}\n  snapshot(key){return {...this.cache.get(key).state};}\n",
      "actual_final_report": "{\"report\":\"已修复 src/session.js：为每个请求尝试独立记录是否已实际启动及是否消费 signal。无人观察者离开时，尚未执行的全新初始暂停尝试会结算为 idle，故重连或已入队恢复均不会首次调用 queryFn；已启动未消费的工作及带缓存数据的暂停刷新仍保持原有可完成/可恢复行为。已用 /runtime/node v16.20.2 运行语法检查和定向生命周期断言：离线卸载后重连、恢复入队后再卸载、重新订阅、多观察者共享的未消费完成、已消费取消，均通过。未安装依赖，未改动配置或测试文件。\"}",
      "visible_messages": [
        {
          "event_line": 5,
          "text": "{\"report\":\"我会定位查询暂停、恢复与观察者卸载的生命周期逻辑，做最小产品源码修复，并用现有测试/定向验证确认行为。\"}"
        },
        {
          "event_line": 10,
          "text": "{\"report\":\"已定位根因：离线创建的暂停尝试未区分“尚未执行”与“已执行但未读取 signal”，重连恢复路径因此会直接首次调用 queryFn。将把取消能力与是否实际启动记录到尝试级别，并仅终结无人观察的全新、未启动初始暂停尝试。\"}"
        },
        {
          "event_line": 19,
          "text": "{\"report\":\"已修复 src/session.js：为每个请求尝试独立记录是否已实际启动及是否消费 signal。无人观察者离开时，尚未执行的全新初始暂停尝试会结算为 idle，故重连或已入队恢复均不会首次调用 queryFn；已启动未消费的工作及带缓存数据的暂停刷新仍保持原有可完成/可恢复行为。已用 /runtime/node v16.20.2 运行语法检查和定向生命周期断言：离线卸载后重连、恢复入队后再卸载、重新订阅、多观察者共享的未消费完成、已消费取消，均通过。未安装依赖，未改动配置或测试文件。\"}"
        }
      ],
      "source": "/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-paused-frozen-experience-followup-20261108_144036/runs/block-3-B/archive"
    }
  ],
  "preserve_success": "All three target relations passed in all three B runs; do not discard initial retirement/idle settlement/queued invalidation, legal cached refresh or started nonconsuming completion.",
  "correct_failure": "Both failing schedules invoked twice rather than the required once; retain expected existing behavior, not relax evaluator.",
  "feedback_exposure": "This training feedback may contain score/standard details. Future maintenance sees only unchanged A plus raw frozen E2, not this feedback, patches or score explanations.",
  "unknowns": [
    "No counterfactual patch was executed or scored in this offline diagnosis.",
    "No causal certainty about experience wording; no universal law for every shared-cache system.",
    "No reference or manually repaired patch supplied."
  ]
}