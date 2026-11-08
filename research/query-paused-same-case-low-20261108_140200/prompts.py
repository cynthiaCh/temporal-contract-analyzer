"""Mechanical responsibility change only; same transformation for both arms."""
OLD='；补丁从独立工作区归档。'
POLICY='原始快照、最终源码、补丁差异、日志及实验结果由外部运行器自动保存。请集中完成业务修复与必要验证，不创建用于实验留档的备份副本、补丁归档目录或结果汇总文件。结束时按现有输出格式简要说明修改与验证结果。'

def adapt_maintenance_prompt(prompt):
    if prompt.count(OLD)!=1:raise ValueError('expected exactly one known historical archival clause')
    return prompt.replace(OLD,'。\n\n'+POLICY,1)

def build_prompt(auto_prompt,experience=None):
    # Apply once to common input, then append the original raw experience unchanged.
    common=adapt_maintenance_prompt(auto_prompt)
    return common if experience is None else common+'\n\n'+experience
