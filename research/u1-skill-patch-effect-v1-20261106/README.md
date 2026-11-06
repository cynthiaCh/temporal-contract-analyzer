# U1开发集内补丁效果归档

入口：REPORT.md、summary.json、behavior.csv、costs.csv。

三份技能与完整prompt已在正式前固定；首次候选选择、未完成独立人工复核与风险见candidate-sources.json/RISK_REVIEW.md。PLAN/protocol/input-control/schedule绑定原始输入和顺序。

六个独立workspace及events/patch/score/model-meter在trials/reports-experiments/<job>/。Agent只看到自身候选工作区；隐藏评分/参考在执行后研究侧运行。

原run.py错误冻结动态manifest，首槽完成后中断。runtime-correction.json、continue_remaining.py及continuation.freeze.json记录唯一显式修正：仅排除操作状态清单整文件摘要，仍检查其中不可变配置及全部源文件/prompt；跳过已完成首槽继续余五槽。没有重跑、换候选、改输入或多于六会话。原协议和异常日志保持。

安全离线复算命令（不调用模型或评分器）：

```sh
python3 -B research/u1-skill-patch-effect-v1-20261106/analyze.py
python3 -B research/u1-skill-patch-effect-v1-20261106/evidence_extract.py
PYTHONDONTWRITEBYTECODE=1 /home/sribd/anaconda3/bin/python3.11 -B research/u1-skill-patch-effect-v1-20261106/verify.py
```

不要重新执行prepare/preflight/execute/continue_remaining；它们不是离线分析入口。结果已结束，无剩余补跑权限。mechanism-review.csv是当前执行Agent的未盲化证据分析；独立人工复核仍未完成。

original frozen-start、paired-K与historical-parent比较在summary中分开。没有用required总分抵消丢失项。新评分和测试仅支持本案描述，不作泛化或因果推断。
