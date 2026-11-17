# GPT6低latent20：相对最初10例的失败分析

仅事后分析，不修改经验、代码修复或测试成绩；Gold观测不得作为后续solver输入。

|组|模型|经验条数|结果|
|---|---|---:|---:|
|最初10|gpt6.1 medium|39|8/10|
|相同精确10本轮|gpt6 medium|73|4/10|
|另外10|gpt6 medium|73|7/10|
|其中新增4core例|gpt6 medium|73|4/4|
|本轮全部|gpt6 medium|73|11/20|

重复10例的TASK、原始source inventory、solver/grader images及各阶段预算完全一致。4个退化集中在autosave React/Vue2、query Vue3和review jQuery。新增机制不是当前主要证据支持的解释；4个新core样本全部通过，但样本小。

本轮8/20因选择输出重复candidate、错误predicate或self-redundancy等校验失败，纠正后仍失败则整个delivery清空。8例中5失败；有交付的12例中8通过。这个关联不能当作经验因果收益估计。对应必要旧经验仍出现在64条候选池中，未交付主要发生在选择/校验步骤。

代表性选择输入：原39条经验正文45240字符，新64条候选206751字符（约4.6倍）。更早GPT6.1在73条bank/64候选的另一组20例没有整体校验丢弃，但case不同，不能量化模型与负担各自贡献。

具体失败链：

- Autosave React/Vue2：校验失败清空经验；Contract没有落实离开前settle的保留义务；patch改为buffer.push，却缺少departure.flush。Gold事后观测缺close/switch/reopen/dispose等效果。
- Query Vue3：经验丢弃，Contract主目标正确；实现取消全部未进入执行的任务，遗漏fresh与cached分支。与正确版本比较，少了previous.status约束；Gold缺cached-paused-background/cached-later-consumption。
- Review jQuery：选择有效但将editor-submit-entry降为weak，未交付提交前持久化建议。Contract和patch遗漏submit前flush；Gold缺提交边界及重入提交效果。
- Query Ruby：交付lazy-shared-cancellation，其适用/反例已区分fresh与cached，实际实现仍过度取消cached任务。说明交付正确经验也不保证正确实现。

8路未出现容量降档，9个失败均正常提交并得到UNDERREACH；当前没有证据将主要差异归因于并发。模型从6.1换6、bank从39增73、候选从39增64同时发生，不能宣称单独因素解释了全部差异。

建议优先缩小每批候选审查负担，按条拒绝不支持/重复项并保留其他已验证项；完整requires/excludes与证据约束继续执行，未评估/unknown项不准入。将保存、提交持久化、确认显示等义务分开覆盖，保留从原始可观测行为推导的约束。再固定gpt6 medium、73经验、同20例与同预算复测。该复测仍为已暴露诊断集。
