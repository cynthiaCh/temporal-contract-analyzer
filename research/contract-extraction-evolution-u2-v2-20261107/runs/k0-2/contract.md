1. 可确认的 Contract
原任务明确要求：文件下载对话框遇到准备服务返回 pending 时，应继续检查；只有收到 ready 后才交付对应文件。这里的 pending、ready 是任务描述中的状态含义，候选源码未给出其具体数据格式。

2. 每条的条件、效果、来源及依据
- 条件：下载对话框正在处理某文件，准备检查结果表示 pending。效果：继续发起后续准备检查，且此时不得将该文件视为已可交付。来源：原任务背景的“keeps checking pending preparation and delivers the file only after a ready status”，足以支持行为要求，但不足以规定重试间隔、次数或调度方式。
- 条件：同一文件的准备检查结果表示 ready。效果：此后才交付该文件。来源：原任务背景的“only after a ready status”，足以支持交付时机，未规定交付的具体机制。
- 当前实现事实，并非业务规范：[usePreparation.js](/workspace/src/usePreparation.js:23) 对任何真值结果都把请求时的 token 加入 completed，且没有安排后续检查；[DownloadDialog.jsx](/workspace/src/DownloadDialog.jsx:6) 使用该 hook，并只渲染 visible/loading 属性。[preparation-api.js](/workspace/src/preparation-api.js:3) 将 token 传给外部 transport；同文件第 10–20 行提供重试调度和取消接口。[BackgroundExportPanel.jsx](/workspace/src/BackgroundExportPanel.jsx:19) 展示另一个界面对假值结果安排重试、真值结果记录完成；这是可参考的实现事实，不能直接当作下载对话框的完整规范。

3. 不能确认的候选要求
- pending/ready 的实际返回值形状，以及是否仍以假值/真值表示：源码只显示现有布尔式判断，缺少新版服务协议。
- 重试间隔、上限、失败处理，以及关闭、重新打开、更换 token 或卸载时对在途请求和重试的精确规则：现有接口和生命周期代码提供线索，但原任务未指定预期效果。
- “交付文件”是否等同于写入 completed，或还需触发浏览器下载：候选源码没有文件交付接口或产品说明。

4. 建议验证范围
建议用明确的 pending、ready 响应序列检查：pending 后会再次检查且不会提前交付；ready 后才交付对应文件。另检查请求与交付所用的文件身份，以及关闭、重开和卸载期间是否发生过期交付或无效重试。上述均为建议验证，尚未执行；即使通过，也不能单独确定服务状态格式、重试政策或真实下载机制。