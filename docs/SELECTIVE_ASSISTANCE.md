# 候选门控：有适用证据才交付 D，否则交付 A

这是基于少量探索数据制定的可解释候选策略，当前没有经过独立任务验证，也没有预测单次修复成功的概率。原有手工 A/D 模式保持原义；只有显式选择 selective 才会应用门控。

## 候选调用范围

1. 任务要求处理 pending/ready、持续检查或轮询；任务目标或可识别的本地依赖中，同时出现可定位的生命周期、保护状态线索，才选择 D。
2. 任务描述初始状态/消息缺失；任务目标或本地依赖存在 connect-before-listen 的具体语法证据，才选择 D。
3. 同时涉及审计/历史保留、重试/取消、乱序/重入等组合行为时，暂时放弃，选择 A。
4. 任务不匹配、扫描不完整、线索空或与任务目标关联不足时选择 A。A 不表示源码安全；D 也不表示缺陷已确认或一定有收益。

门控输入仅为原任务、冻结源码报告和候选源码；不使用 case ID、模型 ID、oracle 结果、失败标识或经验记忆。匹配焦点函数/声明范围，再跟踪最多两层可解析的标识符调用和导入目标；不能因为同文件另一个函数匹配任务，就把受保护消费者的线索算给当前任务。显式保护/保留行为子句不用于寻找焦点入口。词法可达性不是运行时调用关系证明；成员派发、跨语言和同义词关联不足时可能回退 A。

## 使用

仅做任务预筛，不运行模型，也不强制调用扫描器：

```sh
python3 -m temporal_contract_analyzer reports route --task-file TASK.md
```

潜在匹配会返回 `needs_scan=true`，在提供具体报告前仍为 A。扫描后可补充 `--report-id REPORT_ID --store REPORT_STORE --node NODE`，结合归档来源决定 A/D。无支持的任务可在读取报告前直接放弃。

工作台自动冻结一个案例并准备单次选择，增加 `--run` 才实际调用一次模型：

```sh
TCA_BENCH_ROOT=/path/to/temporal-contract-bench \
python3 -m temporal_contract_analyzer reports selective \
  --case-id CASE_ID --model MODEL_ID --effort medium \
  --timeout 600 --node /path/to/node --store REPORT_STORE --run
```

API 为 `Workbench.prepare_selective_case(data)` 或 `POST /api/experiments/selective`；准备后沿用原 `/start`。不接受手动 conditions 或多次重复。案例支持范围、完整解析要求与本地登录/模型选择机制沿用现有工作台。

`routing.json` 冻结决策与理由，记录在 Agent 可见工作区之外；启动前检查未被改变。选 A 时保持既有 A 提示词逐字相同、报告为空；选 D 时交付现有完整 D 层，不额外告诉 Agent 门控理由。没有先运行 A/D 再挑选更好答案的过程。

## 成本与验证范围

任务预筛可以完全不扫描就回退 A，潜在匹配仍需静态检查。工作台为了冻结/归档输入仍对每个输入做原有扫描，因此工作台回放减少的是 D 材料交付，不等于减少相同比例的扫描次数、模型调用数或 token。

`tools/replay_selective_policy.py --matrix MATRIX_JSON --output NEW_DIRECTORY` 只对保存的原始成对 A/D 输出作回放，绝不调用模型。此策略根据同一批4道题提出，其中两个 download 是同源变体；24个模型/强度配置不能当成24个独立任务。该回放既不是新实验，也不是独立验证。

初版回放为固定 A 6/24、固定 D 13/24、候选门控13/24；D材料交付24→18次。输入/输出 token 的旧观测只下降约1–2%。复杂题回退 A 会避开一些部分退步，也会放弃部分收益，不能据此保证每个配置不受损。回放 CSV 同时保留 A/D/选择结果的必需效果缺失与禁止效果触发 ID，以及相对固定 D 和固定 A 的逐项 gained/lost，不能仅靠缺失项总数判断退步。

下一步应先冻结规则，再按来源家族划分新任务验证固定A、固定D和门控；必须保留未调用记录和局部效果取舍。当前证据不足以建立可靠的跨家族成功预测器。
