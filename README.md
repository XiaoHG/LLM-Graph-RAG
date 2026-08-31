# maohua_top

地方性氟中毒智能辅助诊断项目的 Stage4 代码仓库。

## 说明
- `src/`：核心代码
- `cli/`：命令行 demo
- `tests/`：单元测试
- `prompt/`：可复用提示词
- `configs/`：配置文件
- `test_data/`：示例输入数据
- `references/`：项目资料与约束来源

## 环境
- Python 3.10+
- `DEEPSEEK_API_KEY`：报告生成所需
- 可选：`DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_TIMEOUT`
- 可选：`NEO4J_URI`、`NEO4J_USERNAME`、`NEO4J_PASSWORD`、`NEO4J_DATABASE`

## 安装
```powershell
pip install -e .
```

## 测试
```powershell
pytest -q
```

## 运行
生成报告：
```powershell
python cli\report_demo.py --input test_data\input_example.json --output output\report.json --api-key %DEEPSEEK_API_KEY%
```

Neo4j demo：
```powershell
python cli\neo4j_demo.py --node-label Sign --node-name "桡骨嵴轻度增大"
```

## 备注
- `report_demo.py` 读取 `prompt/` 下的提示词文件。
- 当前报告生成版本不接入 Graph-RAG。
- `output/` 用于保存生成结果。
