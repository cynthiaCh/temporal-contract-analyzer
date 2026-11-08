# download-polling-restoration 配对案例编辑源

同一下载轮询事件的三种证据表示。共享任务和验收输入，各表示保留各自源码与修复。

独立单元：`download-polling-restoration`。本 cluster 不新增案例，也不新增独立事故。

| 案例运行目录 | 专属编辑源 |
|---|---|
| [download-polling-restoration-react18](../../case-clusters/download-polling-restoration/arms/download-polling-restoration-react18/README.md) | [arms/download-polling-restoration-react18](arms/download-polling-restoration-react18/) |
| [download-polling-restoration-explicit-react18](../../case-clusters/download-polling-restoration/arms/download-polling-restoration-explicit-react18/README.md) | [arms/download-polling-restoration-explicit-react18](arms/download-polling-restoration-explicit-react18/) |
| [download-polling-restoration-low-cue-react18](../../case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/README.md) | [arms/download-polling-restoration-low-cue-react18](arms/download-polling-restoration-low-cue-react18/) |

每个 `arms/<case-id>/` 都是完整、可直接验证和运行的案例根目录；不同 arm 的源码、oracle、prompt 与 provenance 各自保留，不再抽取 shared 或生成运行副本。

本次提取 10 个共享文件、3 个 ID 模板，全部运行目录内容与提取前一致。

编辑后执行：

```bash
python3 -B clusterbench.py validate download-polling-restoration
```


[全部 clusters](../README.md) · [全部案例](../../CASES.md)

本批从 download-polling-restoration-react18 合成派生九个跨技术栈变体；原案加本批为十个，簇内另有两个既有表示案例不计入本批。验证与来源见 expansion/download-polling-restoration-react18/README.md。所有变体继承同一独立来源单元，没有启动付费解题实验。

Explicit coordination family: `download-polling-restoration-explicit-react18` plus nine synthetic variants (Java, Python, PHP, Ruby, Go, vanilla, Vue 2, Vue 3, jQuery). [Mechanism, plan and actual receipts](expansion/download-polling-restoration-explicit-react18/README.md). Named generation/cancellation preserves foreground and workspace ownership; this family shares the existing source unit and has no solving runs.
