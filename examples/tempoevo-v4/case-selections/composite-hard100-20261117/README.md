# 综合最难100：分层划分草案

状态：只生成清单，未改动现行split，未启动训练或测试。

难度按gpt-6-sol/medium与gpt-6.1-sol/medium原始L通过率等权平均，要求两组均至少1次有效记录；排除缺失/无效记录，不计作失败。按难度、最小样本数降序、case ID排序取100。

共24个真正core类（parent_case_id），10个单例类；因此不能每类严格70/30。草案用最大余数法取70训练/30测试，单例只给训练。

其中27例在两组历史基线均为100%；79例至少一组不足3次有效记录。这是相对难度排序，不是100个均经充分重复验证的难题。

测试草案中10例有已知开发/训练/测试/经验来源暴露，不能作为新鲜holdout。所有测试均优先选择无已知暴露的ID，但部分类不存在这样的候选。

现有39条经验包含历史归并来源，不能宣称仅来自本次70例。若评价从70例学习的效果，应新建空经验库重新训练并审核后冻结；历史开发测试的暴露仍需单独报告。当前划分只是可审查草案，执行前须解决历史role冲突并重新做全部环境/评分对照校准。

|core case|总数|train|test|test已知暴露|
|---|---:|---:|---:|---:|
|async-generator-close-python|10|7|3|0|
|cached-feed-lifecycle-repair-vanilla|1|1|0|0|
|document-submit-snapshot-vanilla|1|1|0|0|
|download-polling-restoration-explicit-react18|1|1|0|0|
|download-polling-restoration-low-cue-react18|2|1|1|0|
|download-polling-restoration-react18|3|2|1|0|
|draft-async-save-handoff-vanilla|1|1|0|0|
|draft-autosave-handoff-order-example-vanilla|4|3|1|0|
|draft-autosave-handoff-precise-rule-vanilla|8|5|3|2|
|draft-autosave-handoff-v2-vanilla|1|1|0|0|
|draft-autosave-handoff-vanilla|9|6|3|2|
|draft-autosave-handoff-vue3|10|7|3|2|
|listener-registration-order-vanilla|1|1|0|0|
|listener-snapshot-order-vanilla|1|1|0|0|
|local-config-readiness-latent-vue2|1|1|0|0|
|local-config-readiness-low-cue-vue2|1|1|0|0|
|local-config-readiness-python|1|1|0|0|
|query-paused-initial-fetch-10266|7|5|2|2|
|review-confirmation-binding-vanilla|6|4|2|0|
|rxjs-asyncsubject-clear-latent-maintenance|8|5|3|0|
|subscription-lifetime-scope-vanilla|5|3|2|0|
|transfer-progress-composition-v4-window-cued|8|5|3|1|
|transfer-progress-maintenance-v2-vanilla|3|2|1|1|
|workspace-draft-projection-latent-vanilla|7|5|2|0|

## 建议采用的历史暴露优先划分

同一100例另生成 exposure-protected-training70.csv / exposure-protected-testing30.csv。测试30例均不在本次扫描发现的训练、开发测试及旧经验来源清单中，且每个测试core都有训练case。为此部分core没有测试，其他core测试比例会高于30%。这仍不等于已认证从未见过：扫描有边界、旧经验逐条来源不完整，且本样本按已有baseline结果选取。

运行建议：使用全新经验库，从这70例重新训练、审核并冻结；测试30例一次提交、Gold仅最终评分，不用测试结果改经验后重新算正式成绩。若继续使用现有39条经验，则应明确报告历史经验迁移设定，不能写成仅用这70例得到的经验。

当前工具对部分非Python/JS源码的结构分析仍为unsupported；清单保留这些case，但新100例执行前必须逐例确认工具/语言覆盖、原始/参考/负例控制和镜像依赖，不能把不支持或基础设施失败当作难题失败。
