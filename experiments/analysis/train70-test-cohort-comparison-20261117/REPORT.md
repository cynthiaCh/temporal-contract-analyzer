# GPT-6.1 medium：训练70与各测试组完整汇总

所有带经验结果均已核对实际protocol/state，模型为gpt-6.1-sol / medium。原100例由训练70＋新测试20＋保留测试10组成。最新复测实际21例，另列，不能称为20例或直接并入原100例。

历史Latent主口径是case等权平均：先计算每个case有效试次通过率，再对有记录的case平均。缺失/无效不补0。Auto-Contract只取真实无经验、自动生成Contract的运行，绝不用历史给定Contract替代。

|集合|例数|原Latent（case等权；覆盖）|仅Auto-Contract（1次Action；有效覆盖）|带经验首个Action|带经验最终|
|---|---:|---|---|---|---|
|训练70|70|51.2%；70/70|25.0%（3/12；覆盖12/70）|87.1%（61/70）|92.9%（65/70；最多3次Action）|
|原100例中的新测试20|20|100.0%；20/20|—（无记录）|95.0%（19/20）|95.0%（19/20；最多1次Action）|
|保留测试10（历史80%）|10|33.3%；6/10|0.0%（0/6；覆盖6/10）|80.0%（8/10）|80.0%（8/10；最多1次Action）|
|最新26–46名复测21|21|16.8%；16/21|15.0%（3/20；覆盖20/21）|71.4%（15/21）|71.4%（15/21；最多1次Action）|

训练70还存在另一份Auto-Contract训练协议的历史子集：覆盖23/70，首轮16/23=69.6%，最多3次Action最终19/23=82.6%。该训练协议带公开检查/失败反馈；不能与表中单Action测试协议合并成一个数字。训练70本身复用了26条历史成功记录并执行44例，并非70例用最终61条经验重新统一跑过。

带经验快照不同：保留10例使用39条，新测试20例使用73条，最新21例使用合并后61条；训练70是动态训练经验并含历史复用。这是历史描述性对照，不是同版本、同覆盖、同期严格消融。Auto-only来自旧V11单Action测试，因此与最新实现也有版本差异。其action预算同为24requests/600seconds，但总准备流程和版本不同。

Auto-only保留10中7例有运行记录，6例有效、1例评分执行无效；最新21中21例都有记录，20例有效、1例评分执行无效。工具无效均不记行为失败。

最新21例与训练70重合11例，与保留10重合6例，与原新测试20不重合；它是历史开发复测，不是新增独立holdout。原100例和最新21例合计121条分组观测、104个不同case；若仅把训练70、最新21和保留10相加，则只有84个不同case。

## 历史有效试次的原始汇总（与case等权不同）

|集合|Latent通过/有效试次|试次加权通过率|给定Contract通过/有效试次（不是Auto）|
|---|---:|---:|---:|
|训练70|175/226|77.4%|135/142；覆盖60/70|
|原100例中的新测试20|93/93|100.0%|54/58；覆盖19/20|
|保留测试10（历史80%）|2/6|33.3%|9/10；覆盖10/10|
|最新26–46名复测21|6/28|21.4%|22/26；覆盖20/21|

## 完整逐case清单

全部70个训练case、原新测试20、保留10和最新21例均在下面列出，CSV另外提供原始次数、两种Auto协议结果、来源路径；summary.json提供输入哈希，evidence.json保留每条实际protocol/state哈希。

|组|case ID|Latent通过/有效试次|Auto单Action|Auto训练≤3次|带经验首轮|带经验最终|
|---|---|---:|---|---|---|---|
|训练70|draft-autosave-handoff-precise-rule-vanilla-port-go|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-precise-rule-vanilla-port-jquery|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-precise-rule-vanilla-port-php|0/1|—|失败|通过|通过|
|训练70|draft-autosave-handoff-precise-rule-vanilla-port-react|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-precise-rule-vanilla-port-ruby|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-precise-rule-vanilla-port-vue2|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-precise-rule-vanilla-port-vue3|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vanilla-port-go|0/1|—|通过|失败|通过|
|训练70|draft-autosave-handoff-vanilla-port-java|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vanilla-port-jquery|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vanilla-port-php|0/1|—|通过|失败|通过|
|训练70|draft-autosave-handoff-vanilla-port-react|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vanilla-port-ruby|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vanilla-port-vue2|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vanilla-port-vue3|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vue3-port-go|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vue3-port-java|0/1|—|通过|失败|失败|
|训练70|draft-autosave-handoff-vue3-port-jquery|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vue3-port-php|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vue3-port-python3|0/1|—|通过|通过|通过|
|训练70|draft-autosave-handoff-vue3-port-ruby|0/1|失败|—|失败|失败|
|训练70|draft-autosave-handoff-vue3-port-vue3|0/1|失败|—|通过|通过|
|训练70|query-paused-initial-fetch-10266-java|0/1|—|失败|通过|通过|
|训练70|query-paused-initial-fetch-10266-jquery|0/1|失败|—|通过|通过|
|训练70|query-paused-initial-fetch-10266-php|0/1|—|失败|通过|通过|
|训练70|query-paused-initial-fetch-10266-python3|0/1|—|失败|通过|通过|
|训练70|query-paused-initial-fetch-10266-vanilla|0/1|失败|—|失败|失败|
|训练70|query-paused-initial-fetch-10266-vue2|0/1|失败|—|通过|通过|
|训练70|transfer-progress-composition-v4-window-cued-go-eval-v2|0/1|失败|—|通过|通过|
|训练70|transfer-progress-composition-v4-window-cued-ruby-eval-v2|0/1|失败|—|通过|通过|
|训练70|transfer-progress-composition-v4-window-cued-php-eval-v2|0/1|失败|—|通过|通过|
|训练70|transfer-progress-composition-v4-window-cued|2/11|失败|—|通过|通过|
|训练70|download-polling-restoration-python3-eval-v2|1/1|—|—|失败|通过|
|训练70|review-confirmation-binding-go|1/1|—|—|通过|通过|
|训练70|review-confirmation-binding-java|1/1|—|—|通过|通过|
|训练70|review-confirmation-binding-ruby|1/1|—|—|通过|通过|
|训练70|review-confirmation-binding-vue2|1/1|—|—|通过|通过|
|训练70|review-confirmation-binding-vue3|1/1|—|—|通过|通过|
|训练70|subscription-lifetime-scope-vanilla-port-react|0/1|通过|—|通过|通过|
|训练70|workspace-draft-projection-latent-vanilla-port-php|1/1|—|—|通过|通过|
|训练70|workspace-draft-projection-latent-vanilla-port-ruby|1/1|—|—|通过|通过|
|训练70|download-polling-restoration-low-cue-react18|6/11|—|—|失败|失败|
|训练70|local-config-readiness-python|10/10|—|—|通过|通过|
|训练70|draft-autosave-handoff-order-example-python3|1/1|—|—|通过|通过|
|训练70|transfer-progress-composition-v4-window-cued-vue3-eval-v2|1/1|—|—|通过|通过|
|训练70|download-polling-restoration-react18|9/11|—|—|失败|失败|
|训练70|async-generator-close-python-port-vue2|1/2|通过|—|通过|通过|
|训练70|transfer-progress-maintenance-v2-python3|1/1|—|—|通过|通过|
|训练70|document-submit-snapshot-vanilla|11/11|—|—|通过|通过|
|训练70|listener-registration-order-vanilla|10/10|—|—|通过|通过|
|训练70|local-config-readiness-latent-vue2|11/11|—|—|通过|通过|
|训练70|workspace-draft-projection-latent-vanilla|11/11|—|—|通过|通过|
|训练70|draft-autosave-handoff-order-example-php|1/1|—|—|通过|通过|
|训练70|subscription-lifetime-scope-vanilla-port-python3|1/1|—|—|通过|通过|
|训练70|subscription-lifetime-scope-vanilla-port-vue3|1/1|—|—|通过|通过|
|训练70|workspace-draft-projection-latent-vanilla-port-jquery|1/1|—|—|通过|通过|
|训练70|cached-feed-lifecycle-repair-vanilla|9/11|—|—|失败|通过|
|训练70|download-polling-restoration-explicit-react18|11/11|—|—|通过|通过|
|训练70|draft-async-save-handoff-vanilla|11/11|—|—|通过|通过|
|训练70|draft-autosave-handoff-v2-vanilla|11/11|—|—|通过|通过|
|训练70|listener-snapshot-order-vanilla|11/11|—|—|通过|通过|
|训练70|transfer-progress-maintenance-v2-vanilla|11/11|—|—|通过|通过|
|训练70|async-generator-close-python-port-java|2/2|—|—|通过|通过|
|训练70|async-generator-close-python-port-react|2/2|通过|—|通过|通过|
|训练70|async-generator-close-python-port-ruby|2/2|—|—|通过|通过|
|训练70|local-config-readiness-low-cue-vue2|11/11|—|—|通过|通过|
|训练70|rxjs-asyncsubject-clear-latent-maintenance-port-go|2/2|—|—|通过|通过|
|训练70|rxjs-asyncsubject-clear-latent-maintenance-port-java|2/2|—|—|通过|通过|
|训练70|rxjs-asyncsubject-clear-latent-maintenance-port-php|2/2|—|—|通过|通过|
|训练70|rxjs-asyncsubject-clear-latent-maintenance-port-vue2|2/2|—|—|通过|通过|
|原100例中的新测试20|workspace-draft-projection-latent-vanilla-port-go|1/1|—|—|通过|通过|
|原100例中的新测试20|async-generator-close-python-port-php|2/2|—|—|通过|通过|
|原100例中的新测试20|subscription-lifetime-scope-vanilla-port-vue2|1/1|—|—|通过|通过|
|原100例中的新测试20|draft-autosave-handoff-vanilla|10/10|—|—|通过|通过|
|原100例中的新测试20|download-polling-restoration-low-cue-react18-port-react|1/1|—|—|通过|通过|
|原100例中的新测试20|download-polling-restoration-vue3-eval-v2|1/1|—|—|失败|失败|
|原100例中的新测试20|draft-autosave-handoff-order-example-react|1/1|—|—|通过|通过|
|原100例中的新测试20|transfer-progress-composition-v4-window-cued-jquery-eval-v2|1/1|—|—|通过|通过|
|原100例中的新测试20|transfer-progress-composition-v4-window-cued-react-eval-v2|1/1|—|—|通过|通过|
|原100例中的新测试20|workspace-draft-projection-latent-vanilla-port-react|1/1|—|—|通过|通过|
|原100例中的新测试20|async-generator-close-python|11/11|—|—|通过|通过|
|原100例中的新测试20|draft-autosave-handoff-order-example-vanilla|11/11|—|—|通过|通过|
|原100例中的新测试20|draft-autosave-handoff-precise-rule-vanilla|11/11|—|—|通过|通过|
|原100例中的新测试20|draft-autosave-handoff-vue3|10/10|—|—|通过|通过|
|原100例中的新测试20|review-confirmation-binding-vanilla|11/11|—|—|通过|通过|
|原100例中的新测试20|subscription-lifetime-scope-vanilla|11/11|—|—|通过|通过|
|原100例中的新测试20|async-generator-close-python-port-go|2/2|—|—|通过|通过|
|原100例中的新测试20|rxjs-asyncsubject-clear-latent-maintenance-port-jquery|2/2|—|—|通过|通过|
|原100例中的新测试20|rxjs-asyncsubject-clear-latent-maintenance-port-python3|2/2|—|—|通过|通过|
|原100例中的新测试20|rxjs-asyncsubject-clear-latent-maintenance-port-ruby|2/2|—|—|通过|通过|
|保留测试10（历史80%）|draft-autosave-handoff-vue3-port-react|0/1|失败|—|通过|通过|
|保留测试10（历史80%）|draft-autosave-handoff-vue3-port-vue2|0/1|失败|—|通过|通过|
|保留测试10（历史80%）|query-paused-initial-fetch-10266-vue3|0/1|失败|—|通过|通过|
|保留测试10（历史80%）|transfer-progress-composition-v4-window-cued-vue2-eval-v2|0/1|无效|—|通过|通过|
|保留测试10（历史80%）|workspace-draft-projection-latent-vanilla-port-vue3|1/1|—|—|通过|通过|
|保留测试10（历史80%）|transfer-progress-maintenance-v2-react|1/1|—|—|通过|通过|
|保留测试10（历史80%）|download-polling-restoration-jquery-eval-v2|—|—|—|失败|失败|
|保留测试10（历史80%）|draft-autosave-handoff-vanilla-port-python3|—|失败|—|通过|通过|
|保留测试10（历史80%）|review-confirmation-binding-jquery|—|失败|—|通过|通过|
|保留测试10（历史80%）|review-confirmation-binding-react|—|失败|—|失败|失败|
|最新26–46名复测21|draft-autosave-handoff-vue3-port-react|0/1|失败|—|通过|通过|
|最新26–46名复测21|draft-autosave-handoff-vue3-port-ruby|0/1|失败|—|失败|失败|
|最新26–46名复测21|draft-autosave-handoff-vue3-port-vue2|0/1|失败|—|通过|通过|
|最新26–46名复测21|draft-autosave-handoff-vue3-port-vue3|0/1|失败|—|通过|通过|
|最新26–46名复测21|query-paused-initial-fetch-10266-jquery|0/1|失败|—|通过|通过|
|最新26–46名复测21|query-paused-initial-fetch-10266-vanilla|0/1|失败|—|失败|失败|
|最新26–46名复测21|query-paused-initial-fetch-10266-vue2|0/1|失败|—|通过|通过|
|最新26–46名复测21|query-paused-initial-fetch-10266-vue3|0/1|失败|—|失败|失败|
|最新26–46名复测21|transfer-progress-composition-v4-window-cued-go-eval-v2|0/1|失败|—|通过|通过|
|最新26–46名复测21|transfer-progress-composition-v4-window-cued-php-eval-v2|0/1|失败|—|通过|通过|
|最新26–46名复测21|transfer-progress-composition-v4-window-cued-ruby-eval-v2|0/1|失败|—|通过|通过|
|最新26–46名复测21|transfer-progress-composition-v4-window-cued-vue2-eval-v2|0/1|无效|—|通过|通过|
|最新26–46名复测21|async-generator-close-python-port-react|2/2|通过|—|失败|失败|
|最新26–46名复测21|transfer-progress-composition-v4-window-cued|2/11|失败|—|通过|通过|
|最新26–46名复测21|async-generator-close-python-port-vue2|1/2|通过|—|通过|通过|
|最新26–46名复测21|async-generator-close-python-port-vue3|1/1|通过|—|失败|失败|
|最新26–46名复测21|draft-autosave-handoff-precise-rule-vanilla-port-java|—|失败|—|通过|通过|
|最新26–46名复测21|draft-autosave-handoff-vanilla-port-python3|—|失败|—|通过|通过|
|最新26–46名复测21|query-paused-initial-fetch-10266-go|—|失败|—|通过|通过|
|最新26–46名复测21|query-paused-initial-fetch-10266-ruby|—|失败|—|失败|失败|
|最新26–46名复测21|review-confirmation-binding-jquery|—|失败|—|通过|通过|
