# Draft 构建与验证报告

日期：2026-10-29。目标：ICPC 2027 Tool Demonstration，IEEEtran 10pt conference。

## 编译结果

- **SUCCESS**：`main.pdf`，正文含 acknowledgment 结束于第 3 页，参考文献单独第 4 页。符合不超过 4 页正文加额外 1 页参考文献的篇幅上限。
- 使用本地 Tectonic 0.17.0（XeTeX）与标准 IEEEtran；没有修改字号、页边距或行距。
- 初次编译修复了 listings 不带 JavaScript 定义的问题，随后添加显式语言定义。最终稿无未定义引用、未定义文献、缺图或 overfull hbox。
- 最终日志仍有 acknowledgment 段落的 underfull hbox 警告（badness 10000 / 7981）；表示两端对齐疏松，未见内容裁切。未屏蔽警告，原文保留在 `compile.log`。
- PDF 的 Times-compatible Nimbus 正文与等宽字体全部嵌入；PDF 约 175 KiB。`evidence/document-checks.json` 保存程序核查结果。
- 已渲染检查正文与参考文献页面。Figure 1 为可编辑 TikZ；Figure 2 是实际中文工作台截图，非设计稿。截图放大跨栏以保留可读性。

## 可复现材料

- Python：127 项测试通过，日志 `evidence/python-tests.log`。
- 插件 runner：9 项通过，日志 `evidence/extension-tests.log`；本次未运行完整 VS Code 宿主测试或跨平台安装认证。
- 行为演示：`node paper/demo/replay.cjs`，仅运行两版合成程序和指定调度；输出 `evidence/demo-traces.json`。
- 静态演示：`/usr/bin/python3 -B paper/scripts/analyze_demo.py`，输出 `evidence/demo-analysis.json`。
- 实际工作台及归档比较：`node paper/scripts/capture_demo.cjs`，使用临时报告库；输出截图、两份报告、作者演示注释及 `demo-comparison.json`。
- 文档检查：`/usr/bin/python3 paper/scripts/check_paper.py`；需要 PyMuPDF，仅用于 PDF 检查，不是分析器运行依赖。
- 运行环境、提交 SHA 与当时源码摘要保存在 `evidence/environment.json`。工作区存在用户先前未提交的功能改动；本次测试针对该工作区，不将 HEAD 当作完整运行源码版本。

## 科研证据边界

当前只有实现回归与合成演示。真实项目有效审查率、开发者理解收益及 Agent 行为改善尚无独立结果。英文正文已按此范围校准，评估写为计划。

本次为 draft 交付，未完成投稿验收：作者信息、公开工具访问、英文使用材料和更充分的独立案例证据仍待补齐。视频为官方建议项。未公开、上传或提交任何材料。
