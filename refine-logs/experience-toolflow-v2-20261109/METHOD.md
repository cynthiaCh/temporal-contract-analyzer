# 当前经验流程 v2：七类义务、多标签与机制条件

v2 接替 v1 的分类与路由口径。v1 以及所有已执行实验仍是历史记录，不能覆盖或重新解释为七类实验。

唯一分类定义：`temporal_contract_analyzer/contract-taxonomy.json`。
公共接口：`taxonomy.py`、`experience_routing.py`，命令行 `taxonomy`、`experience-prompt`、`experience-review-template`、`route-experience`。定义与输入规范见 [CONTRACT_TAXONOMY.md](../../docs/CONTRACT_TAXONOMY.md)。不在本目录复制第二份 codebook。

开发闭环保持“候选 Contract → 与开发标准／行为结果对比 → 反思修订经验 → 回验并记录得失 → 冻结”。测试阶段保持“可见任务与源码／AST → 七类多标签＋机制前提 → 候选经验检索 → 适用性核查 → 原任务＋候选 Contract＋零至一条冻结经验 → 补丁与行为评分”。

七类是 R、O、B、L、I、F、A，不是强制单选；分类依据必须来自当前公开输入。旧 T4、T3 无直接一对一映射。旧经验正文继续保留，但在新流程使用前须另附七类元数据及适用条件。本目录注册表为空，表示尚未迁移条目，不表示旧经验无效，也不表示七类各有可用经验。

本次落地的是共享分类、材料准备、摘要绑定、保守路由与只读展示；模型调用仍由既有运行器负责，未执行新训练／测试。模型、effort、工具权限、预算、来源拆分、接纳门槛和评分版本应在下一次具体实验中先冻结，不能因类别升级暗中变化。一次 Reflection 与官方 GEPA 的优化器分开命名。
