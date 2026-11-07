当前任务仅为代码分析报告。原始维护任务只作为分析背景，不执行维护、不修改候选文件、不运行测试或评分，不产生代码补丁。

<original-task-background>
# Maintenance task

Immediately after opening the presence panel, the initial online-user state is
sometimes missing even though later presence updates appear. Fix the presence
panel while preserving its existing behavior, including workspace navigation.

Do not change the metrics consumer.
</original-task-background>

<analysis-skill>
# 分析技能 K0：任务、源码与证据

此技能只辅助生成代码分析报告，不要求修改代码或执行原维护任务。

1. 先读取作为分析背景的原任务、候选文档与相关源码，分别整理任务目标、明确要求保留的行为和当前实现。不要把函数名或变量名直接当成业务定义。
2. 沿调用关系标记关键入口、回调、等待或调度点、状态写入和对外效果。查到实际生产者与消费者，引用候选工作区的路径和准确行号。
3. 将源码事实、任务或文档要求、原因假设及未知分开。对缺少定义、依赖保证或调用上下文的内容保留未知，不补造接口、业务政策或唯一原因。
4. 说明与任务有关的关键事件之间有哪些已知先后关系，哪些只是可能的顺序；为重要判断给出简短、可检查的证据。
5. 提出需要验证的事件顺序和观察对象，说明验证能回答什么、仍不能回答什么。本轮只提出验证范围，不运行测试、修复或评分。
</analysis-skill>

# 统一分析报告协议

只分析隔离候选工作区的源码与文档。允许只读列出、检索和查看文件；不要执行候选程序。不得读取研究标准、确认记录、评分、参考补丁、历史模型输出或其他运行结果。

返回 JSON 对象，唯一字段为 report，按以下六部分组织：
1. 原任务目标与需要保留的行为；
2. 关键源码事实及路径、行号；
3. 相关事件顺序及其依据；
4. 不同消费者、阶段或效果是否采用不同条件；
5. 能确认的要求、仅有线索的判断及未知项；
6. 建议验证的行为范围。

只要求简短依据和引用，不输出完整内部思维链。区分实现事实、任务或文档要求、假设与未知；不要把建议验证写成已经验证。

report 不超过 6000 个 Unicode 字符（标题、空白、标点、英文均计入）。归档不裁剪；超限、格式错误和失败输出原样保留，不重生成，不以篇幅评价质量。
