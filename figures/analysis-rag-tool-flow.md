# 时序分析 + 自动 RAG：ICPC Tool Track 工具构想

给定代码仓库和修改任务，工具先定位时序相关线索，再自动查找理解这些线索所需的源码，生成可追溯的上下文包，通过 MCP 交给 Coding Agent 核查和辅助修改，最后展示测试结果及修改前后报告。

以下是目标流程；自动检索、上下文打包及其联动尚待实现。扫描线索是待核查证据，不是已确认缺陷；测试结果和报告变化分别展示。

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Arial, PingFang SC, sans-serif", "fontSize": "18px", "lineColor": "#475569", "primaryTextColor": "#172033"}, "flowchart": {"curve": "linear", "nodeSpacing": 28, "rankSpacing": 38}}}%%
flowchart LR
    input["代码仓库 + 修改任务"]
    analysis["① 时序分析<br/>定位异步、重入、生命周期线索"]
    context["② 自动检索与补全<br/>相关函数、导入定义、清理逻辑"]
    packet["③ 证据上下文包<br/>源码引用 + 补充原因 + 未解析项"]
    agent["④ Coding Agent<br/>核查、解释、辅助修改"]
    verify["⑤ 验证与展示<br/>测试结果 + 修改前后报告"]

    input --> analysis
    analysis -->|线索位置与任务| context
    context --> packet
    packet -->|MCP| agent
    agent --> verify

    classDef source fill:#f1f5f9,stroke:#64748b,color:#172033;
    classDef tool fill:#eff6ff,stroke:#2563eb,color:#172033;
    classDef result fill:#f0fdf4,stroke:#15803d,color:#172033;
    class input source;
    class analysis,context,packet tool;
    class agent source;
    class verify result;
```

可按四个方向分工：时序分析；自动检索与依赖补全；MCP 与报告界面；案例设计与效果评估。

核心想法：让静态分析决定值得看的位置，再自动补齐相关源码，为 Agent 提供有来源、可核查的上下文。
