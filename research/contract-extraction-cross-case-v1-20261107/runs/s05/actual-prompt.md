你当前只做 Contract 提取，不执行下面的原维护任务。原任务仅为背景。只允许查阅 /workspace 内候选源码及文档；不得访问历史、研究档案、网络或其他运行。不得修改代码、运行测试、维护评分或生成补丁。

<original-task-background>
The save service is becoming asynchronous: service.commit(snapshot) now returns a Promise for a receipt, or rejects. Update submit to work with it and return a Promise that settles after handling the outcome. Preserve the editor behavior, public methods and other consumers. Search preview is outside this change.

</original-task-background>

<extraction-skill>
# Contract 提取技能 K0

从原任务、候选文档和相关源码中寻找行为要求，区分当前实现事实与应满足的义务。
逐条写明适用条件、相关身份或生命周期，以及必须发生、禁止发生或应保留的效果。
引用可检查的来源，说明来源是否足以支持要求；不要把标识符或现有实现自动当成业务规范。
对于证据不足的要求列为候选或待确认，说明缺少什么；不编造协议、额外政策或唯一实现。
建议验证应对准条件和可观察效果，明确仍不能据此确认的事项，不把建议当作已经验证。

</extraction-skill>

返回JSON对象，唯一字段report，最多6000个Unicode字符。报告固定四部分：
1. 可确认的 Contract；
2. 每条的条件、效果、来源及依据；
3. 不能确认的候选要求；
4. 建议验证范围。

可合并上下文表达，不要求套用固定术语。对当前实现事实作明确标记，不能冒充要求。不补造缺失的产品规格或协议。引用候选路径和准确行号。验证建议不写成已验证。

工具只允许读取候选文件（pwd、ls、rg、cat、nl、sed、head、tail、wc）；命令不能访问 /workspace 以外的文件，不能执行程序、创建文件或使用网络。可使用管道和&&组合上述读取命令。仅返回最终report，不输出内部思维链。
