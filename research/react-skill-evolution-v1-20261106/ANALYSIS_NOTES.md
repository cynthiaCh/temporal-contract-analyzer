# 分析口径及条件断言

不修改run.py的冻结派生向量、原始oracle、选择规则或历史数据。原运行normalize把“原样通过而当前没有同名断言”保守记入original_assertion_losses；在本轮文档结果中，该字段涉及条件断言的发出条件，不能被直接描述成行为失败。

研究侧在全部模型调用结束后核对worker.cjs:99-105：只有renderSubmission(value)的value非null，才添加submission-notice-visit-valid-at-emission。原样在submit-close-on-flush场景会发非null notice，该次断言通过；修复在flush中关闭访问，抑制notice，故不发出此条件断言。当前notice-at-return为null、归档/持久化/同步返回等显式断言均通过，原评分器整体PASS。

分析器保留原机械字段，同时增加original_assertion_failures（仍发出且明确false）与original_assertion_not_emitted（缺项，不自动当通过）。四次文档运行均为后者，不是前者；同一A/B配对没有检查/断言得失。这个分类解释不改变任何评分标准或成绩，也不影响已冻结的技能决定：开发下载实际存在K0 true→K1 false的检查及断言，仍拒绝K1。

同名断言字典是现有派生比较粒度；原始逐次assertions列表完整归档，报告不把缺项、条件发出与明确失败混为一谈。全部保留运行的显式断言没有false，原样已通过检查未丢失。有限评分仍不证明所有未覆盖事件或接口行为等价。
