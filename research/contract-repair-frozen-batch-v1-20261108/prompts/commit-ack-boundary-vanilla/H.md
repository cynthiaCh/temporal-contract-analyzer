# Maintenance task

When saving a profile fails during commit, the page still shows success and navigates away. Fix the issue. Change only direct profile saving; do not migrate the outbox acknowledgement policy.



以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。
只修direct profile saving。commit失败不得显示success或导航，成功结果应在commit之后。保留公开run结果形态以及outbox现有enqueue acknowledgement策略，不将它改成等待delivery。


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器或网络。Node自检使用 /runtime/node，并记录 --version。依赖仅使用已有只读运行时。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。补丁从工作区归档。
