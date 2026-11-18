# 最终实验案例：train70 / test30

本目录保存最终参与实验的完整 100 个案例，只维护这一份划分：

```text
cases/
├── train70/                 # 70 个训练／开发案例，每题一个完整目录
├── test30/                  # 30 个测试案例，每题一个完整目录
├── train70.csv              # 训练顺序，rank 1–70
├── test30.csv               # 测试顺序，rank 1–30
├── selected_100_cases.csv    # 最终 100 题总清单及原始全局顺序
├── split.json               # 唯一划分定义
├── manifest.json            # 案例索引、逐文件 SHA-256 和来源身份
└── verify.py                # 离线完整性检查，不调用模型
```

每个案例目录完整保留原始 `case.json`、初始代码 `base/`、任务与提示 `prompts/`、评分器 `oracle/`、参考实现 `reference/`、负例 `mutants/`，以及该案例原有的文档和来源材料。案例内容与最终实验所用源文件逐字节一致，未因整理而改写代码、提示、参考修复或评分规则。依赖安装和语言工具链由原固定 Docker 环境提供，不包含在案例源码中。

运行模型时只提供该题的公开维护任务和 `base/`；`oracle/`、`reference/` 和 `mutants/` 是独立评分与校准材料，不作为模型输入。案例的最小运行版本、原有启动方式和依赖要求保留在各题原始文档中。

`train70/` 与 `test30/` 的案例 ID 无重叠，测试 30 题与最终结果完全一致。这里的训练指开发／修复及经验处理，不涉及模型参数训练。案例具有历史暴露且部分共享来源机制，该划分不表示独立未见来源测试集。

校验完整性：

```bash
python3 -B cases/verify.py
```

默认实验准备入口依据运行模式使用 `train70.csv` 或 `test30.csv`；`experiments/evaluation-splits.json` 链接到本目录的 `split.json`。最终实验成绩见 [经验库规模消融](../experiments/testing-runs/gpt56-library-size-ablation-20261118/README.md)。
