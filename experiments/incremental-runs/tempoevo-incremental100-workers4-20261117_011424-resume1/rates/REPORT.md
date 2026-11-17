# 固定100例：历史基线与当前训练/测试通过率

100个精确case ID：70训练＋20新测试＋10保留测试。训练复用26条历史成功记录；测试复用旧10例8/10成绩。初始39条历史经验并非只来源于这70例；新20冻结73条，旧10冻结39条。

历史按case等权宏平均，先分别计算每case的有效试次通过率再平均；缺失case不补0。pooled_trial_rate及完整通过数/有效次数见historical-rates.csv。历史跨批次统计，不是同配置统一复跑；给定Contract不能当作Auto-Contract消融。

|集合|gpt6.1 latent（覆盖）|gpt6.1 给定Contract（覆盖）|gpt6 latent|gpt6 给定Contract|
|---|---:|---:|---:|---:|
|全部100|60.3%（96/100）|94.0%（89/100）|40.8%|93.0%|
|训练70|51.2%（70/70）|94.2%（60/70）|36.0%|91.4%|
|新测试20|100.0%（20/20）|95.8%（19/20）|76.7%|100.0%|
|保留测试10|33.3%（6/10）|90.0%（10/10）|3.3%|90.0%|
|测试合计30|84.6%（26/30）|93.8%（29/30）|52.2%|96.7%|

|当前集合|首个Action通过|最终通过|
|---|---:|---:|
|训练70|61/70（87.1%）|65/70（92.9%）|
|新测试20|19/20（95.0%）|19/20（95.0%）|
|保留测试10|8/10（80.0%）|8/10（80.0%）|
|测试合计30|27/30（90.0%）|27/30（90.0%）|

**重要：新20例的当前模型历史latent为93/93有效试次通过，覆盖全部20例；当前19/20不能证明经验提升。此划分的新测试侧明显比训练侧容易。综合两模型选题、测试暴露排除和旧10保留约束不等于对当前模型难度均衡的测试集。**

训练最多3个Action、测试仅1个Action，二者分别报告，不混成单一性能指标。测试30合计包含不同时间、不同经验快照的两组。工具/评分无效不算行为失败；当前20例均正常完成评分。

原始历史试次核对：1050条，1050条至少有1份原始回执SHA匹配，0条缺失/变动。没有新模型调用或评分。

## 逐core结果

|core|例数|训练|新测试|保留测试|
|---|---:|---:|---:|---:|
|async-generator-close-python|7|4/4|3/3|—|
|cached-feed-lifecycle-repair-vanilla|1|1/1|—|—|
|document-submit-snapshot-vanilla|1|1/1|—|—|
|download-polling-restoration-explicit-react18|1|1/1|—|—|
|download-polling-restoration-low-cue-react18|2|0/1|1/1|—|
|download-polling-restoration-react18|4|1/2|0/1|0/1|
|draft-async-save-handoff-vanilla|1|1/1|—|—|
|draft-autosave-handoff-order-example-vanilla|4|2/2|2/2|—|
|draft-autosave-handoff-precise-rule-vanilla|8|7/7|1/1|—|
|draft-autosave-handoff-v2-vanilla|1|1/1|—|—|
|draft-autosave-handoff-vanilla|10|8/8|1/1|1/1|
|draft-autosave-handoff-vue3|10|5/7|1/1|2/2|
|listener-registration-order-vanilla|1|1/1|—|—|
|listener-snapshot-order-vanilla|1|1/1|—|—|
|local-config-readiness-latent-vue2|1|1/1|—|—|
|local-config-readiness-low-cue-vue2|1|1/1|—|—|
|local-config-readiness-python|1|1/1|—|—|
|query-paused-initial-fetch-10266|7|5/6|—|1/1|
|review-confirmation-binding-vanilla|8|5/5|1/1|1/2|
|rxjs-asyncsubject-clear-latent-maintenance|7|4/4|3/3|—|
|subscription-lifetime-scope-vanilla|5|3/3|2/2|—|
|transfer-progress-composition-v4-window-cued|8|5/5|2/2|1/1|
|transfer-progress-maintenance-v2-vanilla|3|2/2|—|1/1|
|workspace-draft-projection-latent-vanilla|7|4/4|2/2|1/1|
