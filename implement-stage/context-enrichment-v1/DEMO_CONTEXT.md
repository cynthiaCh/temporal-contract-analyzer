# 分析线索与源码上下文

报告：r-20261103T152405401010Z-44c66be42cea

Incomplete syntactic context; not proven behavior, complete dependencies or a defect verdict.

仅使用归档源码快照；补充定义不证明实际调用、完整依赖或缺陷成立。

代码字符数：308；最大展开深度：2

## 来源与生成参数

```json
{
  "schema_version": "temporal-context-1",
  "report_id": "r-20261103T152405401010Z-44c66be42cea",
  "input_sha256": "67cbea7697006a83d2400b437b7cec51cee4114595ed97e7720d1f0a34d1cdc8",
  "scan_status": "parsed",
  "finding_ids": [
    "hint-1"
  ],
  "generator": {
    "version": 1,
    "implementation_sha256": "307dde07728feb21e1a8d597ef7ee9f117c580182397f035061c07bbedd6da25"
  },
  "parser": {
    "parser": "@babel/parser",
    "version": "7.29.8",
    "library_sha256": "6969920ae0610df927b6b3e675d1309372c268e36d391652af8e3e0183cbe8f8",
    "node": "v18.17.0",
    "status": "available"
  },
  "aliases": {},
  "limits": {
    "max_depth": 2,
    "max_code_chars": 12000
  },
  "usage": {
    "code_chars": 308,
    "snippets": 3,
    "seeds": 1,
    "definitions": 3
  }
}
```

## main.ts:5–6 · seed

补充依据：[{"kind": "finding-evidence", "finding_id": "hint-1", "evidence_id": "main.ts::e2"}, {"kind": "finding-evidence", "finding_id": "hint-1", "evidence_id": "main.ts::e4"}, {"kind": "local-definition", "symbol": "response", "start_line": 5, "end_line": 5, "from_file": "main.ts", "reference_line": 6}]

```
  const response = await fetch('/api/orders');
  publish(response, columns);
```

## shared.ts:1–4 · definition

补充依据：[{"kind": "import-definition", "module": "./shared", "symbol": "columns", "local_name": "columns", "from_file": "main.ts", "reference_line": 6}]

```
export const columns = [
  { title: '订单编号', key: 'orderCode' },
  { title: '订单名称', key: 'orderName' },
];
```

## shared.ts:6–8 · definition

补充依据：[{"kind": "import-definition", "module": "./shared", "symbol": "publish", "local_name": "publish", "from_file": "main.ts", "reference_line": 6}]

```
export function publish(response: Response, selectedColumns: unknown[]) {
  console.log(response.status, selectedColumns);
}
```

## 未解析项

```json
[]
```

## 范围限制

- 只补充可识别的词法引用与导入所指向的候选定义，未解析项不覆盖所有未知关系。
- 未建模对象成员派发、运行时重赋值、完整调用方、数据流和控制流。
- 仅使用归档扫描范围内的源码，不会从当前工作区读取缺失文件。
- 完整行和声明片段可能含有无关代码；预算只计源码字符，不含说明文字，也不是 token 限制。
