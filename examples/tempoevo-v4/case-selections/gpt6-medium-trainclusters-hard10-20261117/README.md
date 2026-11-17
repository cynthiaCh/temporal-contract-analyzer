# GPT6 medium：训练同cluster最难10例

按训练70的parent_case_id/core匹配；排除已知训练及经验来源的精确ID，再按GPT6 medium原始Latent失败率排名。未知/无效基线不算失败。所有10例均0/3通过，分布在6个训练core；均有历史开发测试暴露。本轮使用最新61条经验，是历史复测，非独立holdout。

|#|case|core|训练同core数量|原Latent通过|
|---:|---|---|---:|---:|
|1|download-polling-restoration-jquery-eval-v2|download-polling-restoration-react18|2|0/3|
|2|draft-autosave-handoff-vue3-port-react|draft-autosave-handoff-vue3|7|0/3|
|3|draft-autosave-handoff-vue3-port-vue2|draft-autosave-handoff-vue3|7|0/3|
|4|query-paused-initial-fetch-10266-go|query-paused-initial-fetch-10266|6|0/3|
|5|query-paused-initial-fetch-10266-ruby|query-paused-initial-fetch-10266|6|0/3|
|6|query-paused-initial-fetch-10266-vue3|query-paused-initial-fetch-10266|6|0/3|
|7|review-confirmation-binding-jquery|review-confirmation-binding-vanilla|5|0/3|
|8|review-confirmation-binding-react|review-confirmation-binding-vanilla|5|0/3|
|9|transfer-progress-composition-v4-window-cued-vue2-eval-v2|transfer-progress-composition-v4-window-cued|5|0/3|
|10|workspace-draft-projection-latent-vanilla-port-go|workspace-draft-projection-latent-vanilla|4|0/3|
