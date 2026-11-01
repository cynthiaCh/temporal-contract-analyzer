# 大纲评审响应

评审：`/root/tool_outline_review`；科研技能 `paper-plan` 的 fresh-context slot；请求 GPT-6-Astra xhigh。结论为同模型家族 provisional，非投稿验收。

| 评审意见 | 处理 |
|---|---|
| 区分提取事实、作者撰写问题、人工判断 | §II 明确 possible change 为 rule-specific question，卡片仅重组已有 evidence，不恢复完整执行链 |
| 行为见证独立于提示数量 | 两个合成版本、固定关闭后完成调度，保存 replay 与双扫描；正文分别描述行为差异和规则保留 |
| 演示理解任务 | Introduction 明确“哪次工作失效，在哪约束延续”；§III 跟随卡片、定位、要求和保护核查 |
| 贡献聚焦表示和工作流程 | 三项能力围绕证据、四问及独立判断、可追溯集成；MCP 作为接口 |
| 测试必须实际留痕 | 127 Python tests 和 9 runner tests 重跑成功；日志和 environment.json 保存源码版本及 dirty checkout 信息 |
| 尽早编译与检查图片 | 使用 IEEEtran 编译，截图放大为跨栏图；最终页数由 BUILD_REPORT.md 报告 |
| 公开交付状态 | 当前内部原型、作者占位和发布待办明确；正文未虚构公开地址 |

独立真实项目和理解对照数据尚未生成；它们是增强方向，不把本次工程检查升级为实际效用研究。
