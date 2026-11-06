已修复初始进度和旧帧回退：[progress.js](/workspace/src/progress.js) 现在先注册监听，再调用 `start()`；乱序完成的旧帧仍进入历史，但不会覆盖较新的显示。入口和显示阶段的归属检查分别位于 [queue.js](/workspace/src/queue.js)。

两种顺序的结论是：

- **`initialPacket` 先导航、后派发**：原访问已结束，该帧不应被原访问接纳，因此不产生其历史或显示。原实现因监听注册过晚会漏掉同步初始帧；修复后的入口检查处理了导航情形。
- **帧已进入解码、随后导航或重试**：该帧已被原尝试接纳，完成后仍记录到原尝试的历史；只有原 visit 和 attempt 仍是当前归属时才显示。旧帧也不能使显示倒退。

这些判断依据可见的 [进度源](/workspace/src/progress-source.js)、[面板生命周期](/workspace/src/panel.js)及 [README](/workspace/README.md)。共享 feed 在重入期间如何给 *其他* 已注册监听者分发同一事件，仍取决于宿主调用顺序；可见文件没有进一步的业务约定。

Node 场景断言已通过，覆盖同步初始帧、两种导航顺序、重试、乱序解码、流式更新和诊断遥测。工作区没有可见测试脚本；`git diff --check` 因 `/workspace` 不是 Git 仓库而无法运行。