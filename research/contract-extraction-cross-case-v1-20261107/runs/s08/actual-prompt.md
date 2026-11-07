你当前只做 Contract 提取，不执行下面的原维护任务。原任务仅为背景。只允许查阅 /workspace 内候选源码及文档；不得访问历史、研究档案、网络或其他运行。不得修改代码、运行测试、维护评分或生成补丁。

<original-task-background>
# Maintenance task

Immediately after opening the presence panel, the initial online-user state is
sometimes missing even though later presence updates appear. Fix the presence
panel while preserving its existing behavior, including workspace navigation.

Do not change the metrics consumer.

</original-task-background>

<extraction-skill>
# Contract 提取技能

从原任务、候选文档和相关源码中寻找行为要求，区分当前实现事实与应满足的义务。逐条写明适用条件、相关身份或生命周期，以及必须发生、禁止发生或应保留的可观察效果。引用可检查的来源，说明来源是否足以支持要求；不要把标识符或现有实现自动当成业务规范。

遇到异步流程，沿一次请求、请求结束后的等待间隙、后续请求和整个活动分别追踪状态。查明状态由谁写入、由谁消费，以及它在各区间呈现什么；区分可见状态事实、整体活动的行为要求和字段含义尚待确认之处。不要从一个字段的当前写法推定它必须独自表达整个活动。

遇到关闭、重开、身份切换或卸载，分别追踪在途回调与已排队工作：确认当前是否安排了后续工作、工作属于哪个活动、取消入口及实际调用位置；再说明在仍挂载、调度仍可触发等条件下可能出现的后续效果。追踪请求捕获的身份与回调修改的共享状态，指出旧回调可能与新活动交错的条件。缺少宿主生命周期、接口保证或产品政策时明确保留未知，不把条件性风险写成已发生的缺陷，也不推定必须采用某种取消或隔离方案。

相邻组件可用于发现状态消费、调度和生命周期边界，但须分别记录其当前行为与目标组件的要求。只有任务或其他规范性来源支持时，才把相邻行为列为应保留的义务。

对于证据不足的要求列为候选或待确认，说明缺少什么；不编造协议、额外政策或唯一实现。建议验证应对准条件、身份、生命周期与可观察效果，明确仍不能据此确认的事项，不把建议当作已经验证。
</extraction-skill>

返回JSON对象，唯一字段report，最多6000个Unicode字符。报告固定四部分：
1. 可确认的 Contract；
2. 每条的条件、效果、来源及依据；
3. 不能确认的候选要求；
4. 建议验证范围。

可合并上下文表达，不要求套用固定术语。对当前实现事实作明确标记，不能冒充要求。不补造缺失的产品规格或协议。引用候选路径和准确行号。验证建议不写成已验证。

工具只允许读取候选文件（pwd、ls、rg、cat、nl、sed、head、tail、wc）；命令不能访问 /workspace 以外的文件，不能执行程序、创建文件或使用网络。可使用管道和&&组合上述读取命令。仅返回最终report，不输出内部思维链。
