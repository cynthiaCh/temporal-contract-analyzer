# 经验库

**全部现行经验都在 [experiences.json](experiences.json) 这一个文件中。**

文件内包含 12 条经验的中文标题、适用条件、建议、保留事项、反例和检查方法。
Iris 接受状态也写在文件内。直接编辑此文件，不使用独立的 decision 文件。

```bash
python3 -B -m temporal_contract_analyzer experience-memory review --store experience-memory/experiences.json
python3 -B -m temporal_contract_analyzer experience-memory freeze --store experience-memory/experiences.json
```

双击仓库根目录的 `launch-experience-review.command` 可打开简洁查看页面。
内容接受不代表迁移效果已经验证。

旧目录中的 `records/`、`sources/` 和其他元数据是历史资料，不是现行经验库。
旧版逐条审核记录已按要求删除；使用上述单文件路径查看和检索现行经验。
