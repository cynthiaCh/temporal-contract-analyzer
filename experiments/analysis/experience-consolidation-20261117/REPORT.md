# 当前经验合并与检索容量建议

只读检查：73条已接受历史记录，68条当前检索经验。未生成、审核或发布任何合并经验，未改经验库，未启动模型或接入外部服务。

## 优先合并候选

|机制|原始ID（候选ID用唯一前缀）|数量|必须保留的差异与义务|
|---|---|---:|---|
|尾随批次合并|trailing-coalescing / editor-trailing-bursts|2→1|重新计时、最新值、空文本、独立文档、后续复用；120ms不是通用常数|
|回调前消费批次|consume-before-callback / editor-batch-reentry|2→1|消费旧批次后才回调，嵌套flush不重复消费，保留回调新建工作与原absence sentinel|
|完整帧新鲜度|result-freshness / progress-full-frame-order|2→1|当前协议定义接收顺序才适用；跨重试的owner范围、审计保留、数值下降、回调前提交watermark|
|审计与显示授权分离|retained-effects / progress-audit-publication|2→1|已接收审计按义务保留，显示前及审计回调后重新校验visit；源代码明确丢弃时不能强加保留|
|持久owner与视图订阅分离|persistent-owner / editor-owner-lifetime|2→1|原始归属、重新打开、独立清理订阅；持久owner不推出同步departure flush，也不适用于瞬态preview|
|终态弹窗的延迟通知|candidate-a272 / candidate-a631 / candidate-acc7|3→1|完成时检查关闭状态；操作调用和原结果返回不受UI guard影响；shell独立；publish及回调重入检查只在目标接口支持时适用|

共6组13条，语义上存在减少7条的空间，即68→61。**这是候选数量推算，并非已完成迁移或行为验证**。persistent-owner及部分modal候选涉及历史未解析替代关系，需要先对照来源和完整旧版本核对，不能直接发布就承诺条数下降。完整ID、待保留义务和谱系提示见audit.json。

## 应保留条件分支的组

- 进度接收6条：c0da/c034是无新增排序要求的maintenance，336b/5f84/4eef/a53e包含显式完整帧新鲜度。建议分别合并同政策的语言变体，保留maintenance和freshness两种适用分支。公共基础是先注册接收、即时退休admission、已接收audit保留、visit和重试记录义务；不能把新鲜度限制无条件套在所有源上。
- active-buffer clear4条：可以抽取共同终态承诺边界，但requires声明、原生存储证据和不可用源码的未知项不同。合并时不能直接union requires，否则会提高门槛而漏匹配；不能丢失undefined与absence区别、重入replay、订阅和实例隔离。
- owned async cleanup4条：共享“cleanup完成后consumer才settle”，但双重失败的错误优先级并不一致。某条要求保留scan失败，另条明确同时cleanup失败的优先级未指定。保留源代码条件，不能升格为全局异常规则。
- local-config readiness2条：保留公共机制与具体分支；一种提供ready接口，一种是timer发布的imperative API。不能把ready()、单次tick、声明式默认值等统一当作就绪或写入的充分条件。

## 容量建议（建议值，未配置）

当前68条正文总计203,494字符，中位数2,980，最长7,557；27条超过4,000字符。字符数不等于token数。

不建议按总数硬删经验。历史归档不设业务上限，仍保留原文和版本。活跃库达到100条或单业务机制出现3–5条重叠经验时，触发整理提示；这是初始运维阈值，不是实验验证的最优容量，不自动拒绝新机制或删除旧经验。

比条数更重要的是候选总token预算、业务义务覆盖、完整适用条件、选择校验失败率和互相矛盾的条目。现有64候选、最多5条/16,000字符交付预算本轮不改。建议每条检索正文逐步整理到约1,000–2,000字符的软目标，保留完整适用条件、限制和义务；案例源码、完整引用、历史观察及重复流程说明作为关联证据留档。不能机械截断以满足长度。

优先验证：同一机制的跨语言case是否召回同一主经验；合法业务分支是否都保留；完整适用条件是否仍可判断；无关义务是否被误用。按冻结经验版本比较检索，不能用测试失败反向改写经验再把该测试当新鲜结果。

## 向量检索建议

当前68条不需要先部署独立向量数据库。先整理知识，再评估向量召回是否减少同义表达/跨语言漏召回。小规模可保存本地向量并精确扫描；embedding生成成本、模型/索引版本和向量缓存需另定，当前未生成。

候选流程：当前已审核/有效版本 → BM25与向量两路召回 → 合并去重/融合排名 → 当前业务义务与完整适用条件重排 → 原文证据校验 → 有界交付。向量相近不能代表requires满足，也不能代表excludes被排除；未知条件继续保持未知。向量索引只是JSON经验库的可重建派生缓存，以内容SHA及embedding模型/配置为键，尊重每轮冻结snapshot，不把历史旧版重新混进来。

若未来需要服务化，可评估pgvector。其官方文档提供精确近邻检索和与全文检索结合的混合搜索方案，并列出RRF/cross-encoder融合；是否提升本项目召回仍需本地验证：[pgvector官方文档](https://github.com/pgvector/pgvector#hybrid-search)。数据库解决索引与存储，知识更新、条件冲突和义务保留仍由经验维护与适用性校验解决。

复现只读清单：`python3 experiments/analysis/experience-consolidation-20261117/audit.py`。audit.json记录源文件哈希，脚本断言检查前后源库未改变。
