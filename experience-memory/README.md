# 分类经验库

**现行经验都在 `library/`，每个主题一个 JSON 文件。**

| 分类文件 | 内容 | 条数 |
| --- | --- | ---: |
| [mechanisms.json](library/mechanisms.json) | 通用机制总结 | 12 |
| [progress-subscriptions.json](library/progress-subscriptions.json) | 初始状态、接收窗口、审计、乱序、重试与资源清理 | 8 |
| [deferred-persistence.json](library/deferred-persistence.json) | 延迟保存、文档归属、提交、确认、通知及组件清理 | 11 |
| [shared-work-cancellation.json](library/shared-work-cancellation.json) | 离线恢复、真实消费、共享观察者、后台策略及尝试隔离 | 6 |

本次统一梳理旧库 71 个版本、54 个经验身份中的 524 条规则，以及原有 12 条
机制总结，归并为上述 37 条经验。版本数量不代表独立经验数量。跨语言的重复
表述合并到同一主题；有条件差异的分支保留在适用条件、反例和检查方法中。
特别保留离开前完成与继续调度、保存通知与移除订阅先后的不同约定，不统一
改成某一种政策。原有 12 条总结仍完整保存在通用机制分类。

每条经验包含稳定 ID、英文标题、标签、适用条件、建议、保留事项、反例和检查
方法。`review` 内联保存审核人、结论和时间，沿用本次会话中 Iris 接受经验的
授权。新增条目没有 `review` 时显示待审核，不进入默认检索。
内容接受不代表已通过新的迁移实验。

训练产生的新候选发布时，按需集中写入 `library/candidates.json`，审核页直接显示，
状态明确为待审核，不进入默认检索，也不改变既有已审核经验的冻结快照。
候选中的 `proposal` 只记录新增、修订或合并及对应经验 ID；发布不会自动覆盖或
删除原条目。详细反思保留在原任务的 `candidate-pool/`，不再复制旧式来源、版本
或 decision 文件。仅补充证据且经验内容不变时，保留原候选记录，不新增重复经验。

双击仓库根目录的 `launch-experience-review.command` 打开审核页面。页面可同时
按分类和审核状态筛选；审核结果只写回该条目所在的分类文件，不生成独立
decision 文件、案例副本或来源档案。直接编辑文件也可维护经验；不同文件不能
使用重复 ID。新主题可增加同格式的分类文件，页面会自动读取。

```bash
python3 -B -m temporal_contract_analyzer experience-memory review --store experience-memory/library
python3 -B -m temporal_contract_analyzer experience-memory freeze --store experience-memory/library
```

旧 `records/`、`sources/` 等仅为原有历史资料，不参与当前分类库读取。
旧单文件 `experiences.json` 已移除，避免出现两个现行入口。

## 训练候选的 Git 保存

未审核、被拒绝和仅补充证据的候选也应进入 Git。外部实验目录不受本仓库 Git 管理，不能作为唯一保存位置。每轮训练结束时，将临时经验、候选反思和证据提案按原始内容归档至 `training-runs/<run-id>/`，附文件哈希和来源清单，并提交 Git。内容修订另以 pending 状态发布到 `library/candidates.json` 供审核；归档目录不作为分类库或默认检索输入。Git 提交不代表审核通过，不得因此修改冻结快照或自动激活经验。
