# 经验开发：真实归档浏览

需要发起新训练或测试时，使用侧栏 **七类训练与测试**（`/experience`），见 [Web v2 流程](EXPERIENCE_WEB_V2.md)。本页仍只读浏览历史归档。

工作台新增 **经验开发**（`/development`）入口，报告库顶部和实验页侧栏均可进入。
页面只读，不启动模型、不运行研究脚本、不重跑评分、不修改经验或确认状态。

## 当前分类口径

当前页面、CLI 和新经验路由接口统一采用 [七类时序义务](CONTRACT_TAXONOMY.md)，允许多标签。旧归档中的 T1–T4 仍显示为历史四类路由，不自动换算，也不改变原实验结果。页面顶部可展开查看七类定义。

## 打开

```sh
python3 -B -m temporal_contract_analyzer reports open
```

点击“经验开发”。若后台仍是更新前的版本，在没有活动实验时使用 `reports stop`
再重新打开；停止报告服务会影响正在运行的网页实验。

Historical studies are kept in a separate archive. The default checkout `research/` may be absent; an empty history is valid. Before starting the service, set
`TCA_DEVELOPMENT_ROOT=/absolute/path/to/research`，指向已有归档根目录。
已运行服务不会自动切换环境变量。页面显示实际读取位置。

## 六类材料

1. **开发案例**：开发/测试角色、任务、冻结源码及候选 Contract。自动 Contract
   保留模型原文；标准要求、确认状态与候选理解不能混同。
2. **修复与反馈来源**：用于经验开发的运行记录。E2 的反馈可能来自旧批次，
   不能把 E2 生成后才运行的 AUTO 对照冒充其开发基线。
3. **差异反馈**：要求值、比较原值、实际值及改善/退步。未知值保持未知，
   `false` 可能是正确的禁止效果。原因解释单列，不自动作为已验证因果。
4. **反思经验**：经验原文、归档的适用/排除条件、反思输入与 E1→本批经验差异。
5. **回验与对照**：每批各组分母、逐运行结果、丢失行为及原始比较。
   开发回验与测试分别展示，不跨批池化。
6. **冻结决定**：接纳/拒绝、未生成经验及其依据。冻结表示固定版本，不能推出
   整题通过、经验有效或已启用生产。没有进入冻结的中断批次保持未启动。

这六项是材料导航，不是所有批次通用的时间顺序。实际顺序见 `actual-schedule.json`。
冻结经验复现批次会显示“本批未执行反思”，并在来源归档存在时提供跳转。

## 当前支持的归档

读取已有 JSON/Markdown，不导入归档中的 Python 模块。适配以下现有结构：

- 带 `stages` 和 `acceptance` 的开发回验批次；
- 带 `groups`、`per_slot` 和 `NEW_EXPERIENCE.md` 的冻结经验对照；
- 带 `development`、`tests` 的分类经验试验，包括准备中断批次。

当前工作区可浏览 query-paused 的 E1 开发、E1 后续对照、E2 修订及复现，
transfer 跨语言开发，以及两案例试验 v1/v2。展示完全来自各批原记录，
不把旧决定自动按新协议重判。未适配的格式不会补造成完成流程。

损坏或超限 JSON 在列表中单独提示。材料只能通过页面生成的白名单读取，
拒绝路径越界和符号链接；不提供配置、凭据或研究脚本的任意文件浏览接口。
正文最多显示前 120000 字符并标记截取；解析 JSON 使用完整内容及独立大小上限，
不把展示截取用于重建或修补模型输出。

## 验证

```sh
python3 -B -m unittest discover -s tests -p test_development_archive.py
node vscode-extension/test/development-browser.cjs
```

浏览器检查沿用已有 Playwright 和 Chrome 环境，使用临时合成归档，
验证步骤导航、复用/中断标记、原文展示、手机布局及 GET-only 访问。
检查不调用 Codex 或模型，也不将合成记录写入正式研究目录。

本版是历史过程展示，不是新的训练执行器。训练控制、经验发布和人工审批按钮
均未加入；后续接入执行应复用已有运行器，并另行记录权限、配置与计量。
