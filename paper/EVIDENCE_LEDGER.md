# Draft 主张与证据台账

写作日期：2026-10-29（Asia/Shanghai）。原始工具时间戳保留原样，不将生成时间当作实验时间序列证据。

| 主张 | 来源 | 可支持的范围 | 不能支持 |
|---|---|---|---|
| 多语言脚本语法与候选关系提取 | `../temporal_contract_analyzer/core.py`、`python_adapter.py`、`../tools/temporal-contract-analyzer/parse.cjs` | 已实现、受声明语义限制的提取 | 完整时序契约推断、全程序正确性 |
| 四问审查卡 | `boundary_cards.py`、`web/app.js`、`test_report_hub.py`；`figures/workbench.png` | 对已有 finding 的证据分类和规则作者撰写问题；人工核查流程 | 自动恢复了完整执行链或用户理解收益 |
| 关系与保护分别记录 | `archive.py`、`web/app.js`、`test_report_hub.py` | 实际功能和实现测试 | 人工意见即实验真值 |
| 共享快照与报告 | `archive.py`、`mcp_server.py`、插件 runner；归档/MCP 测试 | 输入与记录可追溯 | 运输日志证明模型收到/注意/使用 |
| 127 Python 测试通过 | `evidence/python-tests.log` | 当前开发机，`/usr/bin/python3` 3.9.6；127 tests, OK | 新环境安装、实际案例语义正确率 |
| 9 插件 runner 测试通过 | `evidence/extension-tests.log` | `npm test`；9 pass、0 fail | 完整 VS Code 宿主与跨平台认证 |
| 未保护版关闭后发布；保护版该调度不发布 | `demo/`；`evidence/demo-traces.json` | 指定合成程序与一条受控调度 | 任意真实项目修复有效、所有调度正确 |
| 两版保留同样三类提示 | `evidence/demo-analysis.json` | 两版均 parsed；同样三类规则；guard 证据不同 | 提示数相同意味着语义无变化 |
| 工作台截图真实 | `scripts/capture_demo.cjs`、`evidence/demo-archive.json` | 临时报告库、合成源码、实际中文产品界面 | 已实现英文界面或用户研究 |
| 两次归档可比较，guard evidence 改变 | `evidence/demo-archive-guarded.json`、`evidence/demo-comparison.json` | 同一路径同范围，comparable=true；同一 guard-state 规则一增一减，规则种类和总数不变 | 差分结果等于修复证明 |
| 作者演示注释可保存 | `evidence/demo-archive.json` 中 `notes` | 脚本模拟作者核查，显式指出合成要求和证据范围 | 独立参与者评估或盲审标注 |

## 未形成结论的假设

卡片是否优于源码搜索；是否优于信息等量的原始 finding；是否降低理解时间或遗漏；是否改善 Agent 行为；真实项目上的 review relevance；跨语言泛化。正文不得以现在时结果描述这些假设。

## 引用来源

原始 CrossRef BibTeX 保存在 `evidence/bibliography/`，稿件 `references.bib` 仅规范化键名、LaTeX 字符和排版转义。作者与来源的出版信息核对路径：

- Sillito et al. (2006), DOI `10.1145/1181775.1181779`：作者 PDF https://www.cs.ubc.ca/~murphy/papers/other/asking-answering-fse06.pdf 。支持软件演化中的理解问题与关系恢复背景。
- Husák, Kofroň, Zavoral (2025), DOI `10.1109/ICPC66645.2025.00048`：作者单位页面 https://www.d3s.mff.cuni.cz/publications/husak_combining_2025/ 。支持 Slicito 的交互缩小范围、数据流与符号执行描述。
- Raychev, Vechev, Sridharan (2013), DOI `10.1145/2509136.2509538`：作者 PDF https://manu.sridharan.net/files/OOPSLA13EventRacer.pdf 与 IBM https://research.ibm.com/publications/effective-race-detection-for-event-driven-programs 。支持事件驱动竞争、race coverage 及其执行分析定位。
- Ko and Myers (2008), DOI `10.1145/1368088.1368130`：出版者 https://doi.org/10.1145/1368088.1368130 。CrossRef 展示作者名 Amy J. Ko；保留当前元数据，不据记忆改写。支持 Whyline 对程序行为的 why/why-not 提问定位。

DBLP 检索本次返回错误或限流，按 paper-write 的来源链使用 CrossRef 与作者/出版者页面。未声称完成独立 citation-audit 或全面文献查新。

## 会议来源

ICPC 2027 Tool Demonstration：https://conf.researchr.org/track/icpc-2027/icpc-2027-tool-demonstration 。IEEEtran 10pt conference、4+1、非双盲、源码或二进制公开、视频建议 3–5 分钟。日期页：https://conf.researchr.org/dates/icpc-2027 。2026-11-19 AoE 截稿。2027 官方特定要求优先于科研技能中的通用默认项。
