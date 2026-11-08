# Task

The preparation service can now report that a file is still pending before it becomes ready. Update the file download dialog so it keeps checking pending preparation and delivers the file only after a ready status.

原任务明确要求：下载弹窗遇到准备服务返回 pending 时继续检查；只有收到 ready 后才交付文件。这里的 pending、ready 是任务用语；候选源码没有给出它们的具体返回值格式。



Work only from the provided candidate workspace; do not inspect repository history, benchmark materials, or the network. For JavaScript self-checks use this exact runtime: /home/sribd/Downloads/wangshu/temporal-contract-bench-git/results/student-case-expansion-runtime/node18/bin/node. Record its --version. Perform relevant self-checks.


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作。依赖可从 NODE_PATH 指向的只读运行时使用。最终返回 JSON，唯一字段 report，最多6000个Unicode字符，说明实际修改和验证；补丁由工作区差异归档。
