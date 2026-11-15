# 重选：SWE-TempoC latent 困难诊断集（2026-11-16）

本清单替代上一份机制候选25条的推荐地位；旧文件、经验、历史结果和split注册不改写。全部选自冻结242条；未启动训练、测试或模型调用。

## 选择规则

- 排除现有训练1–25的精确case；每条历史latent至少6次有效运行，覆盖至少3个模型/推理力度组合。
- 全模型累计latent通过率不高于70%；若gpt-6.1-sol / medium已有latent记录，则不高于60%。其他模型困难但目标模型已高通过的案例剔除。
- 缺少目标模型latent时，标记为其他模型上的困难候选；不能把Generic成绩或缺失值当作目标模型latent失败。
- 固定机制/父案例配额：提交与身份6、共享取消6、进度/接收窗口5、监听启动2、重入导航3、轮询1、RxJS终态1、异步清理1。提交类内部各取文档、确认、编辑器2条；进度类包含1条不同父案例。
- 家族内优先此前未用于旧26–50的精确case，其次按目标latent、全模型latent与样本数排序；Contract结果只展示，不用于筛选，不只挑Contract成功的案例。
- 70%与60%是本次重新选样的明确难度阈值，不是已有评估协议的修改。

## 规模、证据和限制

25条覆盖8个声明来源、11个父案例；每个声明来源最多6条，语言变体不算独立来源。

其中12条有目标模型低latent的直接记录，13条缺目标模型latent，只能作为待补基线的困难候选。

为了保留25条和上述难度约束，复用旧测试集中的14条；精确旧训练case重叠为0。若要求完全排除旧50条，当前规则仅有12条候选，另存not_in_old50_candidates.csv，不以高通过率案例凑满25。

**这是依据已知历史结果选择的困难诊断集，不能标为未见盲测集。** 经验可能来自相同家族，精确case不同不能证明隔离；未重新认证来源、AST、运行环境或评分适配。

后续如做训练，只能处理允许学习的案例；原split仍保留旧26–50测试预留，本次不修改或绕过它。若做独立测试，另选未暴露来源且不能使用这些历史验收反馈。此处不授权也不启动任一种运行。

## 历史通过率

格式为通过/有效运行；异常排除。目标模型gpt-6.1-sol / medium。全模型率是跨批次描述性累计，不是单模型通过率。历史Contract为给定Contract，非当前Auto-Contract。

| # | Case | 来源 | 全模型latent | 全模型Contract | 目标latent | 旧26–50 |
|---:|---|---|---:|---:|---:|---|
|1|review-confirmation-binding-python3|debounced-submit-flush|3/17 (17.6%)|4/12 (33.3%)|未找到有效记录|否|
|2|review-confirmation-binding-php|debounced-submit-flush|3/14 (21.4%)|7/13 (53.8%)|未找到有效记录|否|
|3|document-submit-snapshot-python3-eval-v2|debounced-submit-flush|4/14 (28.6%)|11/14 (78.6%)|未找到有效记录|否|
|4|document-submit-snapshot-java-eval-v2|debounced-submit-flush|6/15 (40.0%)|12/14 (85.7%)|未找到有效记录|否|
|5|draft-autosave-handoff-vue3-port-vue3|debounced-submit-flush|0/17 (0.0%)|12/15 (80.0%)|0/1 (0.0%)|是|
|6|draft-autosave-handoff-vue3-port-react|debounced-submit-flush|0/16 (0.0%)|12/15 (80.0%)|0/1 (0.0%)|是|
|7|query-paused-initial-fetch-10266-jquery|query-paused-initial-fetch-10266|0/18 (0.0%)|9/14 (64.3%)|0/1 (0.0%)|是|
|8|query-paused-initial-fetch-10266-vanilla|query-paused-initial-fetch-10266|0/18 (0.0%)|9/15 (60.0%)|0/1 (0.0%)|是|
|9|query-paused-initial-fetch-10266-vue3|query-paused-initial-fetch-10266|0/18 (0.0%)|8/15 (53.3%)|0/1 (0.0%)|是|
|10|query-paused-initial-fetch-10266-vue2|query-paused-initial-fetch-10266|0/15 (0.0%)|8/14 (57.1%)|0/1 (0.0%)|是|
|11|query-paused-initial-fetch-10266-ruby|query-paused-initial-fetch-10266|0/15 (0.0%)|7/13 (53.8%)|未找到有效记录|是|
|12|query-paused-initial-fetch-10266-go|query-paused-initial-fetch-10266|0/13 (0.0%)|5/11 (45.5%)|未找到有效记录|是|
|13|transfer-progress-composition-v4-window-cued-go-eval-v2|transfer-retry-abort-handoff|0/16 (0.0%)|11/15 (73.3%)|0/1 (0.0%)|是|
|14|transfer-progress-composition-v4-window-cued-vue2-eval-v2|transfer-retry-abort-handoff|1/16 (6.2%)|12/14 (85.7%)|0/1 (0.0%)|是|
|15|transfer-progress-composition-v4-window-cued-php-eval-v2|transfer-retry-abort-handoff|2/17 (11.8%)|11/13 (84.6%)|0/1 (0.0%)|是|
|16|transfer-progress-composition-v4-window-cued-ruby-eval-v2|transfer-retry-abort-handoff|2/17 (11.8%)|9/11 (81.8%)|0/1 (0.0%)|是|
|17|transfer-progress-maintenance-v2-jquery|transfer-retry-abort-handoff|5/14 (35.7%)|8/13 (61.5%)|未找到有效记录|是|
|18|listener-registration-order-java|listener-registration-order|6/15 (40.0%)|11/15 (73.3%)|未找到有效记录|否|
|19|listener-registration-order-vue2|listener-registration-order|7/13 (53.8%)|11/14 (78.6%)|未找到有效记录|否|
|20|workspace-draft-projection-latent-vanilla-port-java|reentrant-lifecycle-handoff|1/12 (8.3%)|9/11 (81.8%)|未找到有效记录|否|
|21|workspace-draft-projection-latent-vanilla-port-python3|reentrant-lifecycle-handoff|2/14 (14.3%)|12/15 (80.0%)|未找到有效记录|否|
|22|workspace-draft-projection-latent-vanilla-port-vue2|reentrant-lifecycle-handoff|5/16 (31.2%)|11/17 (64.7%)|未找到有效记录|否|
|23|download-polling-restoration-low-cue-react18|download-polling-restoration|12/37 (32.4%)|21/25 (84.0%)|6/11 (54.5%)|否|
|24|rxjs-asyncsubject-clear-latent-maintenance|rxjs-asyncsubject-reentrant-6520|3/6 (50.0%)|5/6 (83.3%)|未找到有效记录|否|
|25|async-generator-close-python-port-vue2|async-generator-close-python|17/25 (68.0%)|2/21 (9.5%)|1/2 (50.0%)|是|

## 历史运行累计（不是25个case的pass@k）

| 范围 | Latent | 给定Contract |
|---|---:|---:|
|全部模型/力度|79/408 (19.4%)|237/355 (66.8%)|
|gpt-6.1-sol / medium（仅有记录的case）|7/23 (30.4%)|26/27 (96.3%)|

## 复现

```bash
python3 -B examples/tempoevo-v4/case-selections/swe-tempoc-hard-latent25-20261116/build_selection.py \
  --history /home/sribd/Downloads/wangshu/tempoevo-swe-tempoc-history-20261116/swe242-per-case-model.csv
```

历史数据源与SHA在historical-inputs.json；其中冻结全部242条的聚合统计与目标统计。原始回执去重和异常分类见相邻tempoevo-swe-tempoc-history-20261116分析目录。只做本地结构、阈值、去重、配额和排除校验，不重新评分。
