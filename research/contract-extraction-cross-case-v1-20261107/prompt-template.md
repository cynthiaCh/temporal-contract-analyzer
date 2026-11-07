你当前只做 Contract 提取，不执行下面的原维护任务。原任务仅为背景。只允许查阅 /workspace 内候选源码及文档；不得访问历史、研究档案、网络或其他运行。不得修改代码、运行测试、维护评分或生成补丁。

<original-task-background>
{{TASK}}
</original-task-background>

<extraction-skill>
{{SKILL}}
</extraction-skill>

返回JSON对象，唯一字段report，最多6000个Unicode字符。报告固定四部分：
1. 可确认的 Contract；
2. 每条的条件、效果、来源及依据；
3. 不能确认的候选要求；
4. 建议验证范围。

可合并上下文表达，不要求套用固定术语。对当前实现事实作明确标记，不能冒充要求。不补造缺失的产品规格或协议。引用候选路径和准确行号。验证建议不写成已验证。

工具只允许读取候选文件（pwd、ls、rg、cat、nl、sed、head、tail、wc）；命令不能访问 /workspace 以外的文件，不能执行程序、创建文件或使用网络。可使用管道和&&组合上述读取命令。仅返回最终report，不输出内部思维链。
