# listener-bootstrap-reentrancy-vanilla

同步解码；修复初始消息漏收，同时保留初始回调中关闭／切换的正确清理。

这是分析过原题 A/D 运行后拆出的开发诊断题，与另一拆分题共享 `listener-registration-order` 来源单元，不是独立事件或留出验证集。候选可见要求位于 `base/README.md`，任务位于 `prompts/maintenance-core.md`；两种报告条件必须收到同一份候选代码和契约。参考修复和评分器均在候选工作目录之外。

实验页可直接搜索案例 ID 或“拆分题”。源码报告由当前分析器生成，不为预期 A/D 结果定制规则。真正的 A/D 表现只有实际模型运行后才知道。

离线验证：

```sh
/usr/bin/python3 -B -m unittest discover -s tests -p test_listener_split.py
```

检查原始代码、参考修复和不完整修复；这些是评分器校准，不是模型实验结果。完整设计、假设和验证记录见 `implement-stage/listener-split-v1/`。
