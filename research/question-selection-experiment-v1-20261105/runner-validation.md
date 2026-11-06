初次执行 `python3 -m unittest discover -s tests -p test_experiment_workbench.py -q`：16项中14通过，2项因Python评分unverified失败。系统python3=3.8.10，合成测试minimum_version=3.9，运行器拒绝使用该版本，未发现其他合格PATH Python。

按上轮运行器已有配置设置 `TCA_PYTHON_BIN=/home/sribd/anaconda3/bin/python3.11`（3.11.3）后重新执行同一mock套件：16/16通过，见runner-tests.log。不改生产或测试代码；不是正式模型重试。实验run.py原已沿用此环境设置；四个实际JS案例的reference/unchanged校准均正常。preflight.json验证24个prompt、命令、共同任务/源码材料与输入摘要。正式模型调用前完成上述验证。
