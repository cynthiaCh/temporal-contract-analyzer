# v1 → v2 执行配置核查

v2为用户授权的整批重做；v1无效输出未进入反馈或比较。生产和全局配置未变，没有新依赖。

- 提取会话从禁用`code_mode_host`改为显式启用，`shell_tool`从默认true改为显式true，确保原有读取工具后端可用。`code_mode`仍false；apps、plugins、多agent等仍关闭。反思仍禁用shell及host。见config-v1-v2.diff、environment-check.json中精确argv与有效features。
- 原request_guard.py逐字复用。候选仍只读挂载为/workspace，模型仍只允许原有读取命令；不新增仓库挂载、网络读取、写入或测试权限。
- 由一次执行整个phase改为单槽分发；仅增加用户要求的执行门，首份真实源码正文读取成功后才继续，不使用质量结果选择。execution_gate.py被冻结。每次工具和输入均独立归档。
- 新增离线有效配置、host二进制启动、真实候选挂载摘要核验；离线只证明配置和文件系统，不证明模型读取。首份正式基线的成功正文读取证据另见first-baseline-gate.json。
- 原模型、低推理、600秒、6000/4000字符、每提取12请求/反思1请求/总49请求不变。原评价表、K0、prompt、schema、候选、task逐字复用。反思模板在正式调用前另行冻结；一次反思，K1原样保存。

OpenAI Docs配置参考：https://learn.chatgpt.com/docs/config-file/config-reference 。公共文档提供通用配置说明；本版本内部host行为以本地CLI有效feature列表、原始失败记录和v2正式读取证据为准，不用文档搜索替代执行证据。
