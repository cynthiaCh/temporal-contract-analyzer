# U1原始源码关系对照样例

这是对**原始冻结candidate-start**的有限关系说明，不是新金标准、补丁建议或运行证明。四份报告a02/a04（K0）、a06/a08（K1）实际看到的都是这一版本；均未获得历史补丁。摘要、prompt、工作区和工具关联见[evidence-links.json](evidence-links.json)。

通俗说：事件到达后开始处理，处理成功后先记历史再尝试显示；切换改变当前访问，取消在有效退订函数执行的路径上移除监听。**这几个动作不是同一时点，也不自动代表业务上合法接纳。**

## 1. 输入在哪里进入处理

- [progress-source.js:26–30](../code-analysis-skill-evolution-v1-20261107/materials/U1/candidate/src/progress-source.js)：start先求值initialPacket（若为函数则调用），非undefined才派发；emit也派发同类事件。
- [progress.js:3–7](../code-analysis-skill-evolution-v1-20261107/materials/U1/candidate/src/progress.js)：listener被调用后取event.detail并调用feed.decode。这是**实现层处理入口**；这里没有业务“合法接纳”标记、current判断或资格协议。
- 同文件9–11行：**原始版本先start，再注册本次新listener，最后返回退订函数。**所以该次注册前的初始派发不会进入这个新listener；共享feed上已存在的其他listener不在此结论范围内。

## 2. 已开始工作在哪里成功交付

progress.js:4–7：

```js
const deliver = frame => { record(frame); receive(frame); };
const decoded = feed.decode(event.detail);
if (decoded && typeof decoded.then === "function") decoded.then(deliver);
else deliver(decoded);
```

同步普通结果直接交给deliver；thenable路径把deliver交给其then方法。只有当后者实际调用deliver时，才进入该成功交付路径；不能把任意thenable都当作有原生Promise调度保证的对象。

在各调用正常返回的路径上，顺序是record→receive。record抛错时后面的receive不保证执行；源码也没有完整拒绝/异常处理。此处没有证明所有解码都会成功、都会异步、可取消或必然完成。实际decode由宿主注入（progress-source.js:10、25；README:10–12）。

[queue.js:11–15](../code-analysis-skill-evolution-v1-20261107/materials/U1/candidate/src/queue.js)进一步区分：record调用宿主recordProgress，无current检查；receive在调用时检查state.current===visit，才调用showProgress。record可能调用外部代码，因此这两个效果也不应假定为不可重入的原子动作。代码事实不自动等同“所有历史都必须保留”的业务政策。

## 3. 切换对输入和完成效果分别做什么

| 环节 | 可确认的原始源码关系 | 不能据此推出 |
|---|---|---|
| current改变 | panel.js:13–15先将current置null并释放旧visit；若未被销毁/重入中止，17–19建立新visit并入队 | current改变本身不是listener入口guard，也不表示监听已移除 |
| handle取消 | releaseVisit在panel.js:4–7清空visit.handle，仅当取得旧handle才cancel | handle尚为空时不能说已调用cancel；所有切换也不保证简单地由A直接变B，宿主可重入 |
| stopProgress取得 | transfer.js:5初为空函数；watch返回后12行才赋其返回值 | 赋值晚不证明期间一定存在可触发的abort或新输入；需要具体驱动及可达性证据 |
| 退订执行 | transfer.js:6–8的abort回调调用当时的stopProgress；13行另有返回后的aborted检查 | stopProgress仍为空函数时不能称已经移除了监听 |
| 实际移除 | 有效退订闭包为progress.js:11的removeEventListener；所给feed在progress-source.js:19–21先移除再通知onDetach | 只有在有效闭包已取得并实际执行、该注册未重新建立的路径上，后续事件才不再经此注册进入旧listener；不是“切换立即移除” |
| 已登记完成回调 | 退订闭包只移除listener，本身不撤销已交给then的deliver；若该完成回调后来调用deliver，仍按原代码交付 | 不保证依赖一定会兑现，也不证明宿主或decoder没有其他取消机制 |
| 历史/显示 | queue.js:12历史不检查current；14行显示检查current===visit，且此检查晚于record调用 | 不能把阻止旧显示当作阻止新输入，也不能把现有无guard当成业务许可 |

引用：[panel.js](../code-analysis-skill-evolution-v1-20261107/materials/U1/candidate/src/panel.js)、[transfer.js](../code-analysis-skill-evolution-v1-20261107/materials/U1/candidate/src/transfer.js)、[progress.js](../code-analysis-skill-evolution-v1-20261107/materials/U1/candidate/src/progress.js)。

## 4. 有限结论与仍缺的证据

能确认：注册/派发、decode/成功交付、current/handle/有效退订是不同位置；记录与显示有不同实现条件。尚不能确认：

1. **业务资格**：在哪个项目事件后不再允许新输入、哪些已开始工作还负有记录义务，需要任务/调用方的明确契约；无guard不是合法性的证明。
2. **完成与取消保证**：需要实际decode/transport及thenable协议，才能讨论错误、拒绝、永不完成或取消后是否仍回调。
3. **具体窗口可达性**：需要原始版本的宿主回调、具体驱动和调用进入/返回顺序。句柄/退订晚赋值只是源码顺序事实，不能独自证明漏洞，也不能据未复现断言安全。

历史e-5b07bf1156dc48d0的补丁把监听移至start之前，并通过progress.ready提前发布handle；其轨迹中A2被多记、之后才detach，是**修改后版本**的观察。原始版本监听顺序和handle发布时间不同。该观察不能作为本样例或原始源码报告必须断言的事实。本轮没有新增运行来证明任何窗口可达或不可达。
