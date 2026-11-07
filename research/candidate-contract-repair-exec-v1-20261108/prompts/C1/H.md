完成以下原维护任务并实际修改候选代码，交付补丁，不仅解释Contract。仅在/workspace内自主执行，保留公共接口和原任务要求。不得读取标准、评分器、隐藏测试、参考修复、历史研究或其他运行，不使用网络。允许在候选工作区内读取、编辑并做相关自检。JavaScript自检使用统一提供的/runtime/node，并记录版本。不要修改候选之外的文件。最终返回JSON，唯一字段report，最多6000个Unicode字符，简述修改和实际自检；实际补丁由工作区差异另行归档。

原任务：
# Maintenance task

Immediately after opening the presence panel, the initial online-user state is
sometimes missing even though later presence updates appear. Fix the presence
panel while preserving its existing behavior, including workspace navigation.

Do not change the metrics consumer.


以下为辅助材料。辅助材料不能替代原维护任务。依据原任务和项目证据核查其适用性；存在冲突或证据不足时回到源码核查，不要盲目执行。

Contract：
- 打开 presence panel 后呈现初始在线用户状态，后续 presence 更新继续呈现。
- 保留 workspace 导航行为，包括发布时同步选择其他房间或隐藏面板，以及后续访问复用 transport。
- 不修改 metrics consumer；其既有行为只统计增量，不计同步 bootstrap。
