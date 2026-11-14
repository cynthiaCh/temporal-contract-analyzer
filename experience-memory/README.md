# 经验库

**全部现行经验都在 [experiences.json](experiences.json) 这一个文件中。**

文件内包含 12 条经验的中文标题、适用条件、建议、保留事项、反例和检查方法。
每条经验的审核人、结论和时间也写在该条目的 `review` 中，不使用独立的 decision 文件。
新增条目未填写 `review` 时为待审核，不进入默认检索。

```bash
python3 -B -m temporal_contract_analyzer experience-memory review --store experience-memory/experiences.json
python3 -B -m temporal_contract_analyzer experience-memory freeze --store experience-memory/experiences.json
```

双击仓库根目录的 `launch-experience-review.command` 可打开审核页面。
页面可按状态筛选，填写审核人并选择接受、需修改或拒绝。保存只更新所选条目的
审核信息，结果直接写回同一个 `experiences.json`。也可以直接编辑文件内容。
内容接受不代表迁移效果已经验证。

旧目录中的 `records/`、`sources/` 和其他元数据是历史资料，不是现行经验库。
旧版逐条审核记录已按要求删除；使用上述单文件路径查看和检索现行经验。
