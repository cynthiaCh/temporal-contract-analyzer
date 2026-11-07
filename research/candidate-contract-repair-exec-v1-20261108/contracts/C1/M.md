
- 打开 presence panel 后，应呈现初始在线用户状态；后续 presence 更新也应继续呈现。原任务明确要求修复偶发缺失的初始状态，并保留既有行为。
- 修复须保留 workspace 导航行为：发布 presence 时可以同步切换房间或隐藏面板；之后再次访问时可以复用同一个 transport。不得修改 metrics consumer。

