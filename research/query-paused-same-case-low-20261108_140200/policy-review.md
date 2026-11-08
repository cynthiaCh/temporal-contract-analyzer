# AI辅助政策核查：未开始查询的暂停尝试与最终观察者退出

来源为原任务、候选README、src/session.js，不以参考实现通过代替业务依据。本例是既有上游来源单元的合成JS表示，已暴露，只作同题开发，不作上游库全等或独立泛化认证。

|关系|可见依据|判断与边界|
|---|---|---|
|首次pending+paused、最后观察者退出|任务明确离线挂载并卸载后的queryFn不可在重连后以live signal启动，独立于refetchOnReconnect；README描述pending/paused、observer scope；source unsubscribe/resume|应终结已退役的首次等待尝试，不仅跳过某次continuation而永久留在paused。Cancellation的可见source cancel会settled、恢复previous并fetchStatus idle；README明确取消应恢复状态并结算原attempt|
|惰性signal消费|README each actual access records consumption；source invoke中的context getter写q.consumed并返回a.controller|消费字段与控制器有不同归属；已保留旧context getter仍写所属query，返回原attempt signal。新paused attempt在实际queryFn入口前不应无据清掉既有query消费事实。这是保留既有语义的源码/契约推导，不从未用a.consumed变量名自动推断新政策|
|已开始/已有缓存后台工作|README unconsumed active work可在view离开后完成，缓存独立于view；source retryCancelled与cancel路径分开|不能把所有无观察者工作一律取消；cached success paused工作与首次pending paused需区分；停止重试不等于撤销已接纳完成|
|结算/回滚/迟到结果|README每次fetch拥有controller及completion，取消恢复previous并settle；source active比较q.attempt===a及a.settled|取消不能仅阻止回调或仅改UI；旧attempt fulfillment不得成为新attempt数据|
|观察者边界|README handles唯一、多观察者共用fetch、unknown unsubscribe inert；source Set/Map|只在最后observer退出触发相应取消政策；不可取消尚有observer的共享work|
|首次启动与resume|README networkMode控制first start；continuation还需focus；source eligible、Promise turn、queued|不能误用refetchOnReconnect来堵retryer，也不能将已获资格的continuation无据改为每次进入重新按最新online撤销；retry/always/offlineFirst语义保留|
|作用域|任务change product source only；README依赖版本/构建配置不属scope；oracle scope-baseline核对package.json及dependencies.lock.json|保持原锁文件、构建/API，不安装新依赖；不把改包配置当修复|

明确事实与未知区分：代码为原生Node16模块及实际Promise；README中的通用跨语言embedding说明不代表本轮替换执行机制。待核查未知包括任意外部宿主抛错、非声明的多线程、完整上游库所有行为；不为这些新增策略。公开source与README能支持本轮义务，AI核查不伪造人工批准。

历史C组的idle失败只是选题线索，本批基线/反馈独立产生；AUTO提取/维护仅能见原任务、候选、K1及机械Contract。完整历史、oracle、参考补丁不挂入actor namespace。所有当前29项原评分及依赖范围检查在冻结后保持不变；回验仅按预定目标改善、原已过行为保留与无据策略审查接纳。
