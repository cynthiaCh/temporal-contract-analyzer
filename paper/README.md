# ICPC 2027 Tool Demonstration draft

英文题目：**Temporal Contracts: Reviewing Asynchronous and Lifecycle Boundaries with Source Evidence**。

这是基于当前实现的初稿。正文描述实际能力和可复现合成演示，未完成的独立评估明确用未来时书写；不含虚构用户研究、真实项目缺陷率或 Agent 改善数字。作者信息为占位，工具和视频尚未公开，不能直接投稿。

## 阅读入口

- `main.pdf`：编译产物（生成后可用）。
- `main.tex`、`sections/`：可编辑英文 LaTeX。
- `TOOL_ENHANCEMENT_ROADMAP.md`：中文工具增强优先级、验收条件与三周安排。
- `EVIDENCE_LEDGER.md`：主张、证据和未完成事项。
- `reviews/`：科研技能要求的大纲/正文审查及响应。
- 根目录 `PAPER_PLAN.md`：篇幅、贡献和引用规划。

## 编译

使用标准 IEEEtran 10pt conference 排版，目标正文不超过四页，加最多一页参考文献。官方要求优先于通用技能的默认页数、匿名与 Related Work 长度要求。

```sh
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

若使用本次下载的本地 Tectonic：

```sh
cd paper
../.aris/tooling/tectonic/tectonic --keep-logs --keep-intermediates main.tex
```

## 复现演示

从仓库根目录运行；需要已安装的 Node 解析器和 Python 3.9+。

```sh
node paper/demo/replay.cjs
/usr/bin/python3 -B paper/scripts/analyze_demo.py
/usr/bin/python3 -B -m unittest discover -s tests
npm test --prefix vscode-extension
node paper/scripts/capture_demo.cjs
```

合成程序只用于展示 `refresh → close → resolve → continuation` 调度。分析器扫描不执行被扫描程序；`replay.cjs` 是单独的演示行为检查。`analyze_demo.py` 重建两版静态报告。截图脚本使用临时报告库和本机 Chrome，记录作者演示注释、在同一路径归档两版并保存可比较结果；不写入正式研究报告库，不修改产品界面。

## 提交前必须补齐

真实作者信息、公开源码或二进制及使用许可、稳定公开链接、独立案例证据、英文使用材料、干净环境安装验证。视频官方建议 3–5 分钟。按实际参与者研究与 AI 使用情况完成相应说明。最终须重新检查 CFP 与页数。
