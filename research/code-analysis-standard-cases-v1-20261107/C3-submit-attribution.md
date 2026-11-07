# C3 草稿：异步提交的入口归属

**AI 辅助编写，全部待用户确认，非独立人工审查。**仅评价原始候选；没有将异步改写后的回调行为写成原始事实。

## 1. 一句话说明

提交时选择的文档、操作者和文本，与请求完成时的当前界面可能不同；成功历史和当前界面提示不能共用一个有效性判断。

## 2. 原任务与保留范围

[原任务](cases/C3/task.md:1)明确 commit 改为返回 Promise／拒绝，submit 要返回处理结果后才 settle 的 Promise，保留接口和其他消费者，预览不变。[README](cases/C3/candidate/README.md:3)规定入口快照、成功后恰好一次审计、失败无成功审计、已接纳提交跨关闭／重开继续；提示只属于当前 visit 的最新提交。这些是候选可见文档契约，尚待本轮人工确认，不以历史隐藏测试补充语义。

来源单元 `audit-commit-attribution`，本地筛选归档提供原始输入；筛选时记录模型调用为 0，但不能据此声称全部历史从未暴露。本轮按开发材料处理，不作独立泛化。与 C2 的辅助模板联系见 [manifest](source-manifest.json)。

## 3. 源码事实表

| ID | 原始源码的有限事实 | 依据 |
|---|---|---|
| C3-S1 | open 建新 visit；edit 改其 text；close 清 current。 | [controller.js](cases/C3/candidate/src/controller.js:3)，3–6、15 行 |
| C3-S2 | submit 无 visit 返回 null；否则生成 owner 并写 latest，用入口 visit 的 doc/actor/text 建对象。这里只复制字段值，未证明任意嵌套值深度不可变。 | [controller.js](cases/C3/candidate/src/controller.js:7)，7–10 行 |
| C3-S3 | done 先 observe，再在 current===visit 且 latest===owner 时 render saved，最后返回 receipt。 | [controller.js](cases/C3/candidate/src/controller.js:11)，11 行 |
| C3-S4 | failed 只在同一双重条件下 render error；try 直接执行 done(service.commit(snapshot))，catch 捕获该同步执行链抛出的异常，没有登记 Promise 完成处理。 | [controller.js](cases/C3/candidate/src/controller.js:12)，12–13 行 |
| C3-S5 | observe 将 snapshot 字段及 receipt.revision 传给 audit.record；该函数不检查当前 visit。 | [observations.js](cases/C3/candidate/src/observations.js:1)，1 行 |
| C3-S6 | 邻近预览按 40 ms 合并，hide 取消待办；helper flush 清旧 pending 后才执行 work。 | [search-preview.js](cases/C3/candidate/src/search-preview.js:3)，3–8 行；[trailing-task.js](cases/C3/candidate/src/trailing-task.js:8)，8–25 行 |

## 4. 两种关键顺序

- **原始表达式可确认，未新运行：**截取 snapshot → 调用 commit → 返回值立刻作为 done 的参数 → observe → 有资格才显示 saved。task 所说的普通 Promise 若代入此处，代码仍立即传 Promise，而不是等其 receipt；之后 Promise settle 不会通过本源码重新触发 done/failed。同步抛出走 catch，异步拒绝不是同一个捕获边界（S2–S5）。缺少真实 service，不能断言具体运行日志或 revision 的实际值。
- **任务／文档支持、需要异步适配分析的顺序：**提交入口取 snapshot → commit 未完成时编辑／close／重开或再次 submit → 原请求成功或失败。成功历史仍归原入口，显示还需区分原 visit 与最新 owner；失败不应留下成功审计（README:3）。这是目标契约下的对照顺序，**不是声称当前 done 已被登记为完成回调**。没有调用方执行证据，不宣称每种交错都已发生。

两者对照能区分“原实现立刻处理返回值”与“新服务最终完成”，不把界面失效推成历史义务取消，也不要求所有提交按全局顺序完成。

## 5. 行为要求及依据

| ID | 要求／待核查关系 | 来源与边界 |
|---|---|---|
| C3-R1 | 适配异步成功／拒绝，submit 返回处理结果后 settle 的 Promise。 | task:1；无当前选择时与旧 null 接口如何协调尚待确认 |
| C3-R2 | 成功才用入口 doc/actor/text 与返回 revision 生成一次历史；失败无成功记录，关闭／重开不抹掉已接纳提交。 | README:3；不是由变量名自行推定的业务含义 |
| C3-R3 | saved/error 仅属于当前 visit 的最新提交，历史与显示资格不同；预览仍 40 ms、hide 丢弃、可复用。 | README:3、5；S3–S6 为对应实现线索，不证明异步目标已满足 |

不采用历史测试预期或参考修复，不规定唯一补丁。

## 6. 未知项

- C3-U1：缺少 service、audit、render 的具体实现及异常／重入约定；不能保证整个成功交付链、重复回调或所有 thenable 的行为。
- C3-U2：doc/actor/text 的类型和可变性未说明；对象字面量不足以证明深度不可变快照，需接口／数据类型证据。
- C3-U3：无选择时 null 与新 Promise 要求的协调、失败 Promise 应 resolve 还是 reject、audit/render 自身失败的政策未明确；不补成标准答案。

## 7. 模型报告评价清单

“满足／部分满足／不满足／证据不足”；接受分散、等价说明。未知不是已经证明安全或缺陷，不以篇幅或总分替代关系判断。

| ID | 只评价候选可见材料支持的内容 |
|---|---|
| C3-A1 | 定位提交入口、visit/owner/snapshot，区分字段快照与深度不可变保证。 |
| C3-A2 | 准确说明当前立即 done、尚无 Promise 完成登记，区分同步抛错和异步拒绝。 |
| C3-A3 | 分开原始顺序与异步契约待验证顺序，不混入历史补丁。 |
| C3-A4 | 将成功审计的入口身份与当前／最新提交 UI 条件分开，有源码及 README 依据。 |
| C3-A5 | 对无选择返回、失败传播、宿主回调和嵌套可变值合理保留未知，不强加排序／取消要求。 |
| C3-A6 | 验证建议涵盖成功／失败、等待中编辑／导航／再提交及预览保留关系，不声称已运行或修复。 |

## 8. 用户确认表

| ID | 关键问题 | 状态 | 用户选择 | 备注 |
|---|---|---|---|---|
| C3-Q1 | 是否确认成功历史保留提交入口身份，关闭／重开只影响提示资格，不取消其历史义务？ | 待确认 | 确认／需要修改／无法判断 | |
| C3-Q2 | 是否同意无选择返回、失败传播、嵌套值可变性及宿主异常政策暂列未知，不作确定扣分？ | 待确认 | 确认／需要修改／无法判断 | |
