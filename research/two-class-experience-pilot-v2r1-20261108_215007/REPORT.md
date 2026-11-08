# v2r1：真实只读命令被误拒后停止

本修订的首个D1提取只启动1个模型请求。请求正常完成，随后只读guard拒绝了rg读取README/docs时的 `2>/dev/null`；CLI被guard终止，归档OK，但没有完整提取结果。checker的组合消息是role/isolation/request distortion，原事件将原因收窄为命令语法误拒，没有角色不一致、请求超限或越界访问的证据。

测试A计划4、启动0、有效评分0；B计划4、启动0、有效评分0。8槽均未启动，不是行为失败。没有新Contract、AUTO、反思、经验或冻结库。1个请求已报告14179 token，用量未知请求0；工程/货币成本未知。本修订触发停止后没有模型重试或补跑。

Typed结构化输出和三个角色schema绑定已通过40项离线检查，但实际生成尚未完成，不能据此宣称语义已经修好。此前v2的一次提取/3请求及全部失败材料保留。当前研究下一版只离线修复了读命令兼容，见相邻v2r2目录；原冻结代码、原始响应、失败会话及计量不改。

详细原事件：diagnostics/read-policy-stop.json。完整计划/实际计量/未启动槽位见summary.json、terminal-test-schedule.json；不能进行A/B效果比较。
