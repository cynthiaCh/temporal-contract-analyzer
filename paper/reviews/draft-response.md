# 正文评审响应

评审：`/root/tool_draft_review`；paper-write 的 fresh-context slot，请求 GPT-6-Astra xhigh。原始完整意见保存在 `draft-review.md`。

原评审结论：**PASS AS A WORKING DRAFT, with minor revisions**；同模型家族 provisional。关闭评审时无未解决 critical / major 项，不代表正式投稿验收。

## 已解决的主要问题

1. 双版本比较缺少完整脚本：新增 `scripts/analyze_demo.py`；截图脚本在同一临时工程路径归档两版、传入 parent ID 并保存比较。实际 comparable=true，同规则的 guard evidence 发生变化。
2. 演示注释引用不存在的要求文档：新增 `demo/README.md`，明确合成来源、人工提供的要求和单一调度范围。
3. MCP/人工意见边界不清：正文与图明确 frozen report/source 通过 MCP，人工审查意见经 workbench 与复制材料交接。
4. 视频强制性：正文已改为计划录制；路线图明确视频 optional，公开源码或二进制是正式要求。

## Minor 项处理

| 意见 | 响应 |
|---|---|
| 架构箭头可能被误读为真实持久化顺序 | 图注明确是 conceptual workflow，scan 在 review 之前归档，人工 notes 另行追加 |
| diagnostics 并非全部 information | 改为 review-hint diagnostics，并说明 incomplete parse 为 warning |
| 截图未展开两项判断 | 保留真实初始卡片截图；已保存作者演示注释。英文演示与展开判断控件的画面列为后续材料增强，不伪造英文 UI |
| 路线图混合正式要求与建议 | 分别列正式交付、竞争力增强、定位增强与审查边界；用户研究不作为人为添加的强制条件 |
| 明确 guard 在哪张卡片中 | 改为 guard-state card，不暗示 effect-after-await 卡片已自动获得所有保护关系 |

## 保留限制

作者信息、公开工具链接、干净环境安装与独立案例待补；理解收益仍为未验证假设。当前可交付 draft，不能直接称为 submission-ready。
