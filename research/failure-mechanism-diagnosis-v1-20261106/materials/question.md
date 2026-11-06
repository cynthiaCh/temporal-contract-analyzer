
根据 README.md:8-26、src/progress-source.js:24-28、src/transfer.js:3-16、src/panel.js:10-34、src/retry.js:4-15 和 src/queue.js:8-20，核对 start 内 initialPacket 函数先触发导航、随后派发 progress，与 progress 已进入解码后才导航或重试这两种顺序：事件接纳、历史记录和当前显示各依赖什么归属及有效性条件？请依据原任务与可见实现判断，并区分已有事实和仍需验证的假设。
