# 训练70例＋GPT5.6-sol medium测试30例总结

这是一套由70个训练ID与30个测试ID组成的100例记录，两组精确ID不重合。模型训练权重没有更新；训练是修复任务、反思并积累可检索经验。训练侧执行模型和测试侧模型不同，预算也不同，不应合算单一通过率。

|集合|模型|case数 / core数|原Latent|带经验首轮|带经验最终|
|---|---|---:|---:|---:|---:|
|训练集|GPT-6.1-sol medium|70 / 24|51.2%，覆盖70/70|87.1%（61/70）|92.9%（65/70），最多3轮|
|测试集|GPT-5.6-sol medium|30 / 14|16.7%（5/30）||82.1%（23/28有效评分）；2例执行异常|

训练70：26条历史成功记录复用，44例实际补跑。最终65通过、5修复耗尽；原Latent为case等权平均，试次加权另为175/226=77.4%。已有历史经验先于本次训练存在，因此不能宣称当前61条经验全部仅来自这70例。

测试30：排除当前70及74个已知训练/经验来源ID，按目标模型原Latent排序。只有25例0/1，补充5例1/1；补充的并列按GPT6/GPT6.1原基线难度选，不使用最近带经验测试成败。30例各只有一次有效目标模型基线。25例零通过组当前18通过、5行为失败、2执行异常；补充5例全部通过。

测试使用冻结61条已接受当前经验，8并发，单次Action24requests/600seconds，总请求上限48，一次最终Gold；无AB、诊断、提炼、经验更新或Gold反馈。30例的队列已经结束，尚有2例未获得有效评分；23/30=76.7%是全部入选样本中已通过的比例，不把两例执行异常计为行为失败。

测试历史给定Contract基线为28/29=96.6%，另1例无效；这是预先给定Contract，不是仅Auto-Contract生成。该列不能替换为自动Contract消融，也不能宣称当前带经验结果优于给定Contract。

## 重合与泛化边界

- 精确训练case ID：0/30重合；与74个已知训练/来源ID同样无重合。
- 当前30例全部来自训练覆盖的14个core；24/30已有历史测试暴露。
- 对197份实际训练original快照核对，完整任务＋公开源码的精确副本0/30，但17/30的任务描述逐字相同。未认证改名/结构/语义近重复不存在。
- 正确定位为同cluster任务变体、跨模型经验迁移的开发复测，不是独立新题泛化或严格零泄露实验。

## 两例执行异常

- transfer-progress-maintenance-v2-vue2：selection阶段，包含sort的只读命令被工具策略拦截；没有Gold评分。
- transfer-progress-composition-v4-window-cued-python3-eval-v2：Action请求返回Bad Request；没有合法最终提交/Gold评分。

## 逐core分布

|core|训练数量|训练通过|测试数量|测试通过|测试失败|测试异常|
|---|---:|---:|---:|---:|---:|---:|
|async-generator-close-python|4|4|1|1|0|0|
|cached-feed-lifecycle-repair-vanilla|1|1|0|0|0|0|
|document-submit-snapshot-vanilla|1|1|0|0|0|0|
|download-polling-restoration-explicit-react18|1|1|0|0|0|0|
|download-polling-restoration-low-cue-react18|1|0|2|2|0|0|
|download-polling-restoration-react18|2|1|2|1|1|0|
|draft-async-save-handoff-vanilla|1|1|0|0|0|0|
|draft-autosave-handoff-order-example-vanilla|2|2|2|2|0|0|
|draft-autosave-handoff-precise-rule-vanilla|7|7|1|0|1|0|
|draft-autosave-handoff-v2-vanilla|1|1|0|0|0|0|
|draft-autosave-handoff-vanilla|8|8|1|0|1|0|
|draft-autosave-handoff-vue3|7|5|2|2|0|0|
|listener-registration-order-vanilla|1|1|2|2|0|0|
|listener-snapshot-order-vanilla|1|1|0|0|0|0|
|local-config-readiness-latent-vue2|1|1|0|0|0|0|
|local-config-readiness-low-cue-vue2|1|1|0|0|0|0|
|local-config-readiness-python|1|1|0|0|0|0|
|query-paused-initial-fetch-10266|6|5|2|0|2|0|
|review-confirmation-binding-vanilla|5|5|3|3|0|0|
|rxjs-asyncsubject-clear-latent-maintenance|4|4|0|0|0|0|
|subscription-lifetime-scope-vanilla|3|3|1|1|0|0|
|transfer-progress-composition-v4-window-cued|5|5|4|3|0|1|
|transfer-progress-maintenance-v2-vanilla|2|2|3|2|0|1|
|workspace-draft-projection-latent-vanilla|4|4|4|4|0|0|

完整100个精确ID见cases100.csv，逐core数字见per-core.csv，原始输入哈希见summary.json。测试原始运行目录：/home/sribd/Downloads/wangshu/tempoevo-gpt56-sol-medium-low30-untrained-workers8-20261117_180752。本总结不调用模型、评分器，不改变历史结果或经验。
