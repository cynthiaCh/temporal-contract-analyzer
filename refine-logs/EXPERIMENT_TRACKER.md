# Experiment Tracker

截至2026-10-29：只完成探索性静态盘点，未实施新提取器、未运行参与者或付费模型。

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| R000 | M0 | baseline inventory | analyzer0.6.0 | 242登记/本地base | 139parsed/72partial/23empty/2待物化/6timeout | MUST | DONE | 无候选执行；无模型；不作效用结论 |
| R001 | M1 | seed regression | V1 candidates | listener/document/transfer | 真实callback seed及无关查询负担 | MUST | PLANNED | 先解决漏效果 |
| R002 | M2 | symbol/context validity | V1 relations | 遮蔽/重赋值/accepted-vs-new | 锚点、错误连接、unknown | MUST | PLANNED | 不自动判业务policy |
| R003 | M2 | equal information | F versus U | 同一canonical payload | 节点/边/上下文/问题逐项一致 | MUST | PLANNED | runner尚未实现 |
| R004 | M3 | source-backed gold | V0/V1 | 12内部控制快照 | relevance/证据覆盖/分歧 | MUST | PLANNED | 作者暴露，不称holdout |
| R005 | M3 | task allocation | S/V0/F/U | 6任务×12参与者槽位 | 每task×condition3回答；每人每条件1或2题 | MUST | PLANNED | 分配表可离线生成；招募与适用研究准备未完成 |
| R006 | M4 | developer pilot | S/V0/F/U | 72回答 | grounded correct fraction、分层错误、时间 | MUST | NOT_STARTED | 不保证功效 |
| R007 | M5 | analysis/report | fixed contrasts | F→U primary | 原始计数、参与者/任务依赖、不确定性 | MUST | NOT_STARTED | 不结果后换指标 |
| R008 | M6 | Agent maintenance | S/V0/F/U | 6任务×4×3=72尝试 | 逐义务、消费者、越界修改、成本 | OPTIONAL | NOT_STARTED | 新runner与后端配置待定；不调用 |

第一批应启动的工作是R001、R002、R003的实现与离线核查；不是直接启动72次Agent实验。
