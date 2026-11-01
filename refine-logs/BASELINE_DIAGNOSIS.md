# 当前分析器的 benchmark 盘点（探索性）

日期：2026-10-29。分析器 0.6.0；只读取候选源码，未执行候选、评分器或模型。

固定清单为242个表示：24 core、218 derived，11个来源/构造单元。全历史 catalog 登记348个材料，两者不能合并为同一分母。

| 扫描状态 | 表示数 | 解释 |
|---|---:|---|
| parsed | 139 | 声明范围内解析完成，不代表时序语义已覆盖 |
| partial | 72 | 多见未支持语言，部分工程混有可解析 JS/TS |
| empty | 23 | PHP 主体扩展名未被当前收集器纳入，不是没有程序或风险 |
| requires_upstream_materialization | 2 | 原生上游 core 需要物化完整候选，不能按零提示处理 |
| scan_timeout | 6 | 本次剩余扫描的20秒时限，保留为未完成 |

139个完整解析表示中，37个零 finding。22个本地core均完整解析，其中2个零 finding；其余2个core为原生上游任务。

22个core共74条 finding；其中只有15张卡的 affected effects 槽有引用，36张卡的 protection 槽有引用。有提示的20个core中，10个的全部卡均没有 effect 槽引用。**有引用也不意味着它就是语义相关效果：局部临时变量写入也可能计入。** 这些是表示统计，不是召回率、精度或缺陷检出率。

| 代表案例 | finding | 带 effect 引用卡 | 暴露的缺口 |
|---|---:|---:|---|
| listener-registration-order-vanilla | 7 | 1 | 注册、解码、发布、重入所有权散在不同函数/文件，当前未闭合 |
| document-submit-snapshot-vanilla | 3 | 1 | capture 与旧 UI 是不同效果；有些所谓 effect 仅是 origin/receipt 局部写入 |
| transfer-progress-maintenance-v2-vanilla | 4 | 0 | 已接受审计应继续、退休 UI 应停止，当前没有直接呈现这对效果 |
| draft-autosave-handoff-v2-vanilla | 1 | 0 | 离开前持久化与预览取消不能共享政策 |
| workspace-draft-projection-latent-vanilla | 2 | 0 | editor 局部检查与调用方 projection/history 的边界不同 |
| local-config-readiness-latent-vue2 | 0 | 0 | 子组件 API 发布与父组件调用关系未建模 |
| local-config-readiness-low-cue-vue2 | 0 | 0 | 同一覆盖缺口；不能称为第二个独立事故 |
| async-generator-close-python | 1 | 0 | 返回点被指出，资源所有权、关闭完成及退出路径仍需核查 |

## 执行与解释边界

- 初次并发线程扫描在内嵌完整 RxJS 的材料处持续运行，已中止本次自有进程并保留已完成报告。随后复用本轮报告，以独立子进程和20秒上限完成剩余盘点。
- 不同条目存在并发、缓存和超时策略差异；elapsed_seconds不作为公平性能比较。完整上游库与显式局部范围需另做串行测量。
- runtime 标签不总等于源码构成。例如 Java/Ruby 派生任务也可能内嵌完整 TS 库。6个超时反映的是本次给定范围与资源限制，尚未定位为算法缺陷。
- 扫描器未读取 oracle 或历史结果生成报告；研究者另外阅读了 manifest、rubric 和 reference 来设计实验，后续需披露作者暴露。
- 本次全量盘点之后，不能把这些表示称为本研究者未见样本；内部冻结测试也不消除既有暴露。
- 历史 `tool-report-pilot-v1` 的36个槽位均 NOT_STARTED，不能作为已完成对照。
- benchmark README 指出匿名发布版已独立维护于 `/Volumes/Extreme/ICPC/swe-tempoc`。本次按用户指定使用历史研究仓库作为设计证据，不将它自动视为当前公开版，不修改二者。

原始数据见 `evidence/bench-inventory.json`、`evidence/baseline-summary.csv`、`evidence/baseline-scans/`；复现脚本为 `scripts/inventory_bench.py`。
