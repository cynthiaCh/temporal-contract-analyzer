{
  "shard_id": "generator_sol",
  "assigned_unit_ids": ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"],
  "covered_unit_ids": ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"],
  "status": "complete",
  "candidates": [
    {
      "id": "S1",
      "lens": "L1",
      "name": "效果证据覆盖导航",
      "position": "主要属于 10/29 已有方案执行，不应另称全新方法。",
      "question": "这个函数有哪些值得核查的效果？哪些尚未进入任何审查材料？",
      "mechanism": "先从参数调用、成员写入、效果名称等独立提名，再显示每个候选是否连接到边界、上下文、保护及需求依据；没有 finding 也保留入口。",
      "build_steps": [
        "复用已有 events 和 binding 标签，生成不依赖 finding 的效果候选。",
        "为每个候选记录已关联与未解决的证据槽，同时保留纯查询候选。",
        "增加覆盖列表和源码跳转，明确区分未提名、未连通、未审查。"
      ],
      "prior_difference": "Slicito 通过缩小范围组合数据流与符号执行；这里针对效果候选暴露材料缺口。但独立效果种子已在本项目计划中。",
      "pilot": "CPU、无模型：人工先标注两个外部项目的 12 个小函数，再比较 V0/V1 对相关效果的遗漏及新增无关候选。若遗漏几乎不减少、阅读负担明显增加，否决。",
      "days": "4–6",
      "risk": "低至中",
      "strongest_objection": "枚举更多节点并不等于覆盖更多业务契约；无法从候选全集推出完整性。",
      "reuse": ["core.enrich", "parser events", "boundary_cards.cards", "现有源码导航"]
    },
    {
      "id": "S2",
      "lens": "L2",
      "name": "同一工作中的不同效果，分别审查取消策略",
      "position": "属于现有 effect×boundary×scenario 方案的核心落地，不是新方向。",
      "question": "退休前已接受的工作应该完成哪些效果、停止哪些效果？取消监听能否改变这个答案？",
      "mechanism": "把取消分成停止新接收、已接受工作继续、各效果是否允许，需求由仓库依据和人工确认提供。",
      "build_steps": [
        "允许对同一回调中的 record、publish、notify 分别建审查单元。",
        "记录接受工作、退休边界和效果之间的候选顺序，无法恢复接受身份时显示 unknown。",
        "按情境填写允许、禁止、待确认，并绑定需求原文及源码引用。"
      ],
      "prior_difference": "PromiseKeeper 建模 promise 执行与反模式；本候选关注业务上同一已接受工作中的不同效果义务。差别成立需要真实维护实例。",
      "pilot": "CPU：选 6 个小实例，每例至少两个效果、两种接受时机；独立人工答案验证工具能否保留“历史记录继续、当前界面通知停止”的分裂判断。若仍只能给整回调统一标签，否决。",
      "days": "5–7",
      "risk": "中",
      "strongest_objection": "业务策略主要依靠人填写，工具可能只把人工答案存成表格。",
      "reuse": ["已有卡片", "archive.annotate", "parameter_callback 标签", "已有情境题"]
    },
    {
      "id": "S3",
      "lens": "L3",
      "name": "补丁改变了哪些时序关系？",
      "position": "新增主方向；高上限候选，建议优先。",
      "question": "提示数没变时，补丁是否把 guard 移到了真正暂停点之后？哪些未修改的消费者因此需要重新检查？",
      "mechanism": "比较有限、可追溯的时序关系，而不只比较 finding 签名；输出关系变化及经已知调用边连接的未修改消费者。",
      "build_steps": [
        "限定一个机制：局部 capture/guard/await/effect 的顺序与词法控制区域。",
        "跨版本对齐稳定作用域和事件，对新增、删除、改位的关系输出前后源码证据。",
        "沿已有唯一直接调用候选扩展一跳，列出未修改消费者及无法解析的边界。",
        "在现有 compare 页面展示关系变化和影响范围，保留 unknown，避免声称行为等价或修复成功。"
      ],
      "prior_difference": "Caprese 用历史共变与动态依赖推荐影响位置；Collector-Sahab 在 diff 中附运行状态差异；本候选给出有界、静态的时序关系变化及其证据。必须进一步检索语义差分领域。",
      "pilot": "CPU：冻结 12 个补丁对，包含 guard 前后移动、无关重排、别名未知、仅上游变化。对照旧 compare，检查能否找到真实关系变化，并避免把格式变化当变化。若必须引入全程序分析才能处理多数样本，停止。",
      "days": "8–11",
      "risk": "中高",
      "strongest_objection": "若只是语句位置差分，技术贡献薄；若试图恢复实际时序，又可能超出三周能力。",
      "reuse": ["core.compare", "event.scope/block/conditions", "candidate_call_target", "归档快照", "现有比较界面"]
    },
    {
      "id": "S4",
      "lens": "L4",
      "name": "Vue API 发布到首次使用的证据链",
      "position": "已有路线图 P2 的具体领域化支线；当前未实现。",
      "question": "父组件调用表单 API 时，这一实例是否已经发布 API？重新挂载后拿到的是否还是旧实例？",
      "mechanism": "只建模一种明确的发布/使用协议，展示发布、保存引用、首次调用、卸载清空四类节点。",
      "build_steps": [
        "选择一种协议，例如项目中实际存在的 register 回调，不混合推断所有 Vue 模式。",
        "在父子组件之间建立显式 props/event/回调连接；动态组件和多实例无法区分时保留未知。",
        "给发布前使用、实例替换后旧引用提供可回溯材料，并加入正确使用负例。"
      ],
      "prior_difference": "Sahand 面向运行中的全栈异步交互；本候选面向单一 Vue API readiness 协议的源码证据。不能仅以 Vue 界面作为区别。",
      "pilot": "CPU：从外部 Vue 工具库选择 4 组真实发布/使用点，再用 4 个对照变体验证能否区分正常注册、过早使用和旧引用。若多数必须解析模板或组件实例 points-to，收缩或否决。",
      "days": "9–13",
      "risk": "高",
      "strongest_objection": "当前解析器不建模模板与跨组件实例；新的协议识别可能成为脆弱的定制规则。",
      "reuse": ["Vue SFC 提取", "Babel 事件", "call_links", "卡片与插件跳转"]
    },
    {
      "id": "S5",
      "lens": "L5",
      "name": "让测试解释一个时序反例",
      "position": "新增动态侧车方向，需保持与静态扫描分离。",
      "question": "哪个具体交错使这条保护失效？现有测试是否真正经过了这个交错？",
      "mechanism": "为一个效果绑定两种可控顺序及实际结果，把执行见证映射回边界和源码，而非提供通用时间线。",
      "build_steps": [
        "仅支持已有测试中可控的 deferred promise 或显式测试钩子。",
        "记录开始、暂停、取消/切换、恢复、效果五类事件及顺序。",
        "以同输入两种调度并排解释差异，展示断言覆盖的关系和未经过的关系。"
      ],
      "prior_difference": "NodeRacer 已经利用 happens-before 引导延迟来发现竞态；本候选不以延迟调度本身主张新意，贡献候选是把见证与静态审查问题、测试断言闭合。",
      "pilot": "CPU：3 个已有最小测试，人工指定两个调度；检查工具是否能指出“测试执行过函数但未执行危险顺序”。若只得到普通日志时间线，否决。",
      "days": "7–10",
      "risk": "中高",
      "strongest_objection": "可能只是 NodeRacer/AsyncG 的展示层；钩子侵入和框架差异也会吞掉时间。",
      "reuse": ["源码锚点", "高级测量 witness 结构", "现有卡片", "报告库"]
    },
    {
      "id": "S6",
      "lens": "L6",
      "name": "哪些历史审查结论需要重看？",
      "position": "新增、较稳妥的维护工具方向。",
      "question": "这条 sufficient 判断依赖的 guard、需求或调用关系变了，为什么旧意见仍显示在这里？",
      "mechanism": "为人工判断记录明确的证据依赖；新版本只判定依赖是否改变，不自动迁移安全结论。",
      "build_steps": [
        "保存判断引用的源码区域、关系、需求依据和分析版本指纹。",
        "跨版本对齐并标记依赖未变、依赖变化、无法追踪，保留原始报告不改写。",
        "生成最小重审队列，说明具体是哪项依赖变化；一跳间接依赖无法保证完整时明确显示。"
      ],
      "prior_difference": "Caprese 推荐变化影响位置；本候选追踪已存在的人工作答为何失效。它比现有插件清除旧定位、报告绑定源码哈希更细，但不能把证据未变写成结论仍正确。",
      "pilot": "CPU：制作 10 个版本变化，其中局部源码不变但被依赖 helper 改变，以及纯格式变化；核查重审队列遗漏与误失效。若只能全报告作废，区别度不足。",
      "days": "5–7",
      "risk": "中",
      "strongest_objection": "人工没有列出的依赖仍会漏；保守失效可能制造大量重审负担。",
      "reuse": ["archive.annotate", "报告/输入哈希", "core.compare", "历史快照", "现有核查记录"]
    },
    {
      "id": "S7",
      "lens": "L7",
      "name": "Python 清理请求与清理完成审查器",
      "position": "新的窄语言工具支线。",
      "question": "cancel、close、finally 已经出现，但退出函数前资源真的完成清理了吗？",
      "mechanism": "区别清理请求、清理开始、等待完成、异常传播，只覆盖局部且对象绑定明确的 asyncio 模式。",
      "build_steps": [
        "识别 task.cancel 后等待 task、await aclose、finally 中 await 等有限模式。",
        "跟踪同一局部绑定；重赋值、逃逸、shield 与共享所有权单独显示未知。",
        "展示每条退出路径缺失的完成证据，不把 finally 的存在当作保证。"
      ],
      "prior_difference": "PromiseKeeper 分析 JS promise 生命周期；本候选关注 Python 取消和资源清理完成的差别。还需专项检索 asyncio 缺陷检测工作。",
      "pilot": "CPU：8 个短 asyncio 实例，用事件计数确认调用返回时清理是否结束，包含正确等待与错误遗漏。若静态材料无法区分主要正负例，否决。",
      "days": "6–9",
      "risk": "中",
      "strongest_objection": "容易退化为现有 linter 的 missing-await 规则；真正困难的是所有权及嵌套取消。",
      "reuse": ["python_adapter", "lifecycle_patterns", "await/resource_scope/finally 事实", "卡片"]
    },
    {
      "id": "S8",
      "lens": "L8",
      "name": "从 API 生命周期协议开始读仓库",
      "position": "新增 onboarding 方向；新意风险较大。",
      "question": "第一次接手这个 API，何时能调用、谁能取消、什么算结束，应先读哪几个位置？",
      "mechanism": "由开发者声明少量、带来源的协议边，工具把真实调用点绑定为满足、缺证据或不适用的阅读任务。",
      "build_steps": [
        "为一个真实 API 录入 3–5 条来源可查的发布、使用、取消、完成关系。",
        "利用唯一 import/lexical binding 找直接调用者，不能确定目标就退出自动关联。",
        "输出最短阅读顺序和每项缺失依据，允许跳回实现及测试验证。"
      ],
      "prior_difference": "Slicito 提供可组合分析与定制理解视图；这里把协议问题与仓库入口结合。仅增加协议卡片不足以形成独立研究贡献。",
      "pilot": "CPU：一个陌生小库、两个 API；先独立形成协议答案，再检查工具是否减少遗漏关键入口，且不会把示例中的偶然顺序当规范。找不到明确协议来源即停止。",
      "days": "5–8",
      "risk": "中高",
      "strongest_objection": "像人工编写的交互式文档；协议编写成本可能超过导航收益。",
      "reuse": ["import/call_links", "源码快照", "需求依据字段", "报告和 VS Code 导航"]
    }
  ],
  "errors": [
    "Sahand 给定作者 PDF 两次抓取超时；其差异描述仅依据父任务提供的范围，不作为本槽独立核验结论。",
    "Whyline 作者 PDF 抓取失败，候选没有依赖其细节主张。",
    "未运行任何候选、试验、测试、付费 API 或 GPU 作业；未修改文件。",
    "工期为单作者工程原型、聚焦验证和演示的估计，不含完整参与者研究；没有完成新颖性认证。"
  ]
}

来源支持的发现（5 项）：

1. 现有 `boundary_cards.cards()` 逐 finding 投影，并只在 finding 已有 evidence 内寻找效果；`core.compare()` 比较 finding 及事件签名，不直接比较任意事件间的顺序关系。这支持 S1 的已有计划定位和 S3 的具体切入点。
2. 10/29 `REFINEMENT_REPORT.md` 已明确独立效果种子、有限 symbol/context 和情境核查。因此 S1/S2 应当作为已有路线执行候选；不能用于制造“八个全新点子”。
3. [Slicito](https://arxiv.org/abs/2503.15675) 已组合范围缩小、跨过程数据流与符号执行；通用切片加界面不足以成为本工具的清晰区别。[PromiseKeeper](https://www.franktip.org/pubs/oopsla2018promisekeeper.pdf) 已有动态 promise 图和反模式。
4. [Caprese](https://arxiv.org/abs/2606.21187)、[Collector-Sahab](https://arxiv.org/abs/2212.11077)、[ChangeGuard](https://arxiv.org/abs/2410.16092) 已覆盖影响推荐、运行差分和配对执行。S3 必须聚焦“具体时序关系变化及未修改消费者的审查依据”，不能泛称语义 diff。
5. [NodeRacer](https://cs.au.dk/~amoeller/papers/noderacer/) 已进行 happens-before 引导的延迟探索；[EventRacer](https://www.sri.inf.ethz.ch/publications/raychev2013effective) 已处理事件竞态与 race coverage。[AsyncG 原文](https://atlarge-research.com/pdfs/2019-nodejs-async-graphs-hsun.pdf) 首页标注 **CGO 2019**，应修正父任务中的 ICPC 2019。

本槽倾向：**S3 为主候选，S6 为工期失败时的备选；S1/S2 是必要基础，避免同时包装成额外贡献。**