# 写作证据与范围

这是 ICPC 2027 Tool Track draft，不是已完成的独立效用研究。

核心流程：源码扫描 → 有限定的语法线索 → 四问卡片 → 人工补充仓库依据并分别判断关系和保护 → 可追溯历史报告。CLI、VS Code 和 MCP 为同一分析器提供入口。

已核查源码：README.md；docs/REPORT_CENTER.md；docs/MEASUREMENT_WORKBENCH.md；docs/PAPER2_START.md；core.py、boundary_cards.py、lifecycle.py、reentrancy.py、archive.py、mcp_server.py；vscode-extension/src/runner.js；相关单元测试。

关键限制：名称线索不确定 API 身份；词法顺序不确定可达性；有限静态候选调用关系不确定对象实例或完整调用链；Vue 模板、响应式依赖和 watcher 调度未建模；人工确认关系不等于缺陷；提示变化不等于修复；MCP 返回不等于 Agent 实际使用。完整 E/T/L/H 是人工声明的机械校验，非自动契约推断。

本次稿件不移用 Paper 1 的历史结果。单元测试只验证实现行为，合成调度只证明指定示例的行为；两者都不能支持理解收益、真实缺陷检出率或跨项目泛化主张。

可复现验证将放在 evidence/；公开工具地址、视频、真实作者信息和独立评估仍待提供。本地初稿保留明确 Draft 标识，不能直接称为 submission-ready。
