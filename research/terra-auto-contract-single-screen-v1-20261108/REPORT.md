# 单案例 Terra/medium 自动Contract筛选：离线停止

最终推荐：**证据不足**。尚未产生Terra/medium自动Contract维护结果，不能认定难例、稳定易例或E1适用对象。全批正式模型调用0，无提取、维护、E1、替换案例或补跑。

## Task 1：只选此case及最终准入缺口

事前唯一选定`download-polling-restoration-python3-eval-v2`。cluster canonical是react18，E1历史来源是low-cue arm u02；本例登记为canonical家族的非explicit Python/asyncio派生，eval-v2已暴露开发修订，不是独立来源，也未参加近期explicit/Vue2/Vue3或transfer的同条件比较。它没有已找到的版本匹配固定K1自动Contract/Terra-medium维护记录，因此可用于筛选该条件的空白，而不是预先称难例。

历史Terra/medium对当前case分别有一次裸任务PASS、一次人工Contract PASS；实际run、prompt及原始评分已保存于history/。Qwen/其他模型结果仅列historical-context.json，不作为Terra难度证据。原始未修改代码UNDERREACH只是校准；服务/工具/上限异常也没有被合并成有效模型失败。原任务、3份候选文件、manifest、source-record及评分器版本均关联冻结于materials/cohort/source。

候选可见的生命周期政策充分：DialogResource.close→invalidate（generation增加、取消timer/retry、清loading），reopen新代，response/retry检查disposed/generation；WorkspaceJob.close只隐藏、工作继续，start和dispose按自身原行为保留。没有把low-cue旧关闭政策争议移植过来，也没有因作者确认栏空白机械阻断。

**最终缺口在另一项独立评分要求。** 原任务只明确pending持续检查、ready后交付。README说明异步false/true、外部调度及ownership，没有定义loading字段必须独自表达整个等待区间。候选DialogResource.pending却明确执行`self.state['loading']=False;self.publish()`。现有worker.cjs:30的`poll-pending-keeps-loading-N`断言要求每个pending间隙同时`loading=true,retryScheduled=true,completed=[]`，并进入整体PASS。仅从“loading”命名、相邻后台状态或参考补丁不能补出该字段规范；等待由retryScheduled/其他组合表达的可能性尚未被可见资料排除。

因此，初步admission.json中的生命周期/校准PASS，不能作为完整评分政策准入。最终final-admission.json明确覆盖为STOP_POLICY_BASIS_INSUFFICIENT，policy-gap.json保存具体来源、原断言及未知。没有删掉该评分项、过滤分数、补隐藏要求、改任务、增加人工Contract或选择第二例。

## Task 2：实际调用、校准及成本

已完成8次零模型原评分校准：unchanged=UNDERREACH；bounded reference=PASS；retry-without-invalidation、timer-not-cancelled、same-token-generation、premature-ready均UNDERREACH；duplicate-delivery和shared-dialog-policy均UNDERREACH_AND_OVERREACH。原始stdout/receipt完整保留。这证明评分可复现并能区分参考与错误变体，**不能证明全部断言都有当前任务可见依据**。

已使用修复后的读取后端零模型重放本例全部源码/文档正文，提取副本只读、研究路径隐藏，模型目录支持检查通过。为Python源码正文证据将记录后缀从.js换为.py；没有修改模型权限或旧读取门。认证及运行目录在Git之外，离线profile已删除。

准备配置为维护gpt-5.6-terra/medium、提取gpt-6-sol/low，priority显式；report上限6000 Unicode字符、事件输出16MiB。计划仅x01提取→r1→r2，最多60请求，提取12/600秒，维护24/600秒。PLAN及材料已冻结；尚未发起任何模型请求就因规范缺口停止。配置“可用目录支持”不冒称已实际调用/认证服务可用。

实际提取0/1，维护启动0/2、有效0/2；r1/r2均NOT_STARTED，成功率为null而非0%。正式模型请求/token/会话耗时均0；没有基础设施失败槽位，也没有模型行为失败。原始校准、正文读取和文件操作是本地准备成本，校准秒数见summary.json；主聊天准备/分析token不可取得，明确排除而非计0。无核验单价，不估货币。

准备脚本曾假设source-record.md，而本例实际为source-record.json；仅修正来源文件复制并校验原记录SHA，保留说明，没有重复校准、调用模型或覆盖历史。此元数据准备错误与正式工具/服务失败不同。

## Task 3：后续适用性及证据限制

本批的有效维护分母为0，无法应用“两次失败/一过一败/两次通过”的行为筛选规则。按预先规则归入证据不足。不能凭原代码校准失败、Qwen失败、历史人工Contract通过或可见生命周期结构就称为Terra自动Contract困难候选。

暂不推荐将它直接投入固定E1效果对照：完整评分仍含未充分说明的字段政策，可能把“未获规范”误当“未落实经验”。本批到此结束，不追加E1、不生成经验/技能、不运行GEPA、不换题、不扩大规模；没有Future enhanced组可拼接。后续若另有合法匹配任务与已明确规范，需独立立批、重新运行基线，不能把本轮离线校准或审查当对照结果。

分析为AI辅助，不冒称独立人工复核。旧历史、经验、评分器、生产和全局配置摘要始末核验不变；HEAD及Git差异记录见protection-check.json。未创建提交，归档无auth.json/凭证，零模型准备的临时认证目录已清理。Contract未生成状态在contracts/STATUS.json；实际prompt不存在，prompts仅是未执行模板/提取计划，不冒称模型收到过。所有3个未启动槽位及预算保留。

建议Git commit subject/body见COMMIT_MESSAGE.txt；不创建提交。
