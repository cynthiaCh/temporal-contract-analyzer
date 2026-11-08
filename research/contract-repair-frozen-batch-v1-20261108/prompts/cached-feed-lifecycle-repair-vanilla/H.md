Fix the activity panel's startup and navigation lifecycle.

Opening a feed backed by a warm cache sometimes leaves the first batch missing,
although later activity appears. During quick feed changes or closing and
reopening the panel, rows or the count can also appear for a previous visit.

Correct these timing problems while preserving normal live updates, history
recording, public APIs and the existing rendering adapters. The independent
metrics consumer is outside this repair.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。
接收warm cache首批和后续增量。更换选择或hide后旧visit不再产生可见输出，同feed重用仍是新visit，当前监听继续工作。paintRows可同步导航或返回layout Promise；count只在paint完成且visit仍当前时显示，普通live count仍需保留。已接纳batch解码完成后history仍记录；移除监听不撤销已开始解码/绘制。metrics只看增量，保持其现有策略、API和payload。


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器或网络。Node自检使用 /runtime/node，并记录 --version。依赖仅使用已有只读运行时。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。补丁从工作区归档。
