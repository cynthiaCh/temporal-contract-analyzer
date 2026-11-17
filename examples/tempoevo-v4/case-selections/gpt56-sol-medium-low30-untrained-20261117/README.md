# GPT5.6 sol medium：未训练低通过率30例

排除当前70训练和全部已知历史训练/经验来源ID，按目标模型原始Latent有效试次排名。只有25例0/1，其余均1/1；为满足30例，用GPT6/GPT6.1原始基线难度打破全通过候选的并列，补5例并明确标记。全组历史5/30通过（16.7%），全部仅一次有效基线，不能把0/1当作真实失败概率的可靠估计。已有测试暴露只作披露，不以带经验结果选题。

|#|case|core|原Latent|补充项|历史测试暴露|
|---:|---|---|---:|---|---|
|1|draft-autosave-handoff-vue3-port-react|draft-autosave-handoff-vue3|0/1|False|True|
|2|draft-autosave-handoff-vue3-port-vue2|draft-autosave-handoff-vue3|0/1|False|True|
|3|query-paused-initial-fetch-10266-vue3|query-paused-initial-fetch-10266|0/1|False|True|
|4|transfer-progress-composition-v4-window-cued-vue2-eval-v2|transfer-progress-composition-v4-window-cued|0/1|False|True|
|5|workspace-draft-projection-latent-vanilla-port-go|workspace-draft-projection-latent-vanilla|0/1|False|True|
|6|workspace-draft-projection-latent-vanilla-port-vue3|workspace-draft-projection-latent-vanilla|0/1|False|True|
|7|download-polling-restoration-vue3-eval-v2|download-polling-restoration-react18|0/1|False|True|
|8|transfer-progress-composition-v4-window-cued-jquery-eval-v2|transfer-progress-composition-v4-window-cued|0/1|False|True|
|9|transfer-progress-composition-v4-window-cued-react-eval-v2|transfer-progress-composition-v4-window-cued|0/1|False|True|
|10|workspace-draft-projection-latent-vanilla-port-react|workspace-draft-projection-latent-vanilla|0/1|False|True|
|11|download-polling-restoration-java-eval-v2|download-polling-restoration-react18|0/1|False|False|
|12|download-polling-restoration-low-cue-react18-port-jquery|download-polling-restoration-low-cue-react18|0/1|False|False|
|13|draft-autosave-handoff-order-example-ruby|draft-autosave-handoff-order-example-vanilla|0/1|False|False|
|14|listener-registration-order-php|listener-registration-order-vanilla|0/1|False|False|
|15|listener-registration-order-python3|listener-registration-order-vanilla|0/1|False|False|
|16|transfer-progress-maintenance-v2-vue2|transfer-progress-maintenance-v2-vanilla|0/1|False|False|
|17|draft-autosave-handoff-precise-rule-vanilla-port-java|draft-autosave-handoff-precise-rule-vanilla|0/1|False|True|
|18|draft-autosave-handoff-vanilla-port-python3|draft-autosave-handoff-vanilla|0/1|False|True|
|19|query-paused-initial-fetch-10266-ruby|query-paused-initial-fetch-10266|0/1|False|True|
|20|review-confirmation-binding-jquery|review-confirmation-binding-vanilla|0/1|False|True|
|21|review-confirmation-binding-php|review-confirmation-binding-vanilla|0/1|False|True|
|22|review-confirmation-binding-react|review-confirmation-binding-vanilla|0/1|False|True|
|23|transfer-progress-composition-v4-window-cued-python3-eval-v2|transfer-progress-composition-v4-window-cued|0/1|False|True|
|24|transfer-progress-maintenance-v2-jquery|transfer-progress-maintenance-v2-vanilla|0/1|False|True|
|25|workspace-draft-projection-latent-vanilla-port-vue2|workspace-draft-projection-latent-vanilla|0/1|False|True|
|26|async-generator-close-python-port-php|async-generator-close-python|1/1|True|True|
|27|subscription-lifetime-scope-vanilla-port-vue2|subscription-lifetime-scope-vanilla|1/1|True|True|
|28|transfer-progress-maintenance-v2-react|transfer-progress-maintenance-v2-vanilla|1/1|True|True|
|29|download-polling-restoration-low-cue-react18-port-react|download-polling-restoration-low-cue-react18|1/1|True|True|
|30|draft-autosave-handoff-order-example-react|draft-autosave-handoff-order-example-vanilla|1/1|True|True|
