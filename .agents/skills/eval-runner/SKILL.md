---
name: eval-runner
description: >
  Omni-Brain 评测运行技能。运行知识库检索评测集，对比基线，生成评测报告。
  用于在系统能力变更后检测回归，以及定期了解当前能力水位。
  触发关键词：跑一下评测、测一下检索效果、有没有变差、回归测试
metadata:
  author: omni-brain
  version: "1.0"
  platform: [codex, antigravity, opencode]
---

# 评测运行技能（eval-runner）

## 触发条件

- 检索引擎或摄入流水线修改后
- 用户要求了解当前能力水位
- 怀疑某次更新导致性能下降

## 执行流程

```bash
# 运行全量评测
python eval/runner.py --suite all

# 只运行知识检索评测集（最常用）
python eval/runner.py --suite knowledge_retrieval

# 对比基线（检测回归）
python eval/runner.py --suite knowledge_retrieval --compare-baseline

# 生成详细报告
python eval/runner.py --suite all --report
```

## 报告解读

- **召回率 < 0.8**：检索引擎需要调优（调整 BM25 参数或图扩展策略）
- **延迟 > 1s**：索引或图结构可能需要优化
- **与基线相比下降 > 5%**：可能存在回归，需要排查最近的变更

## 更新基线

当评测结果经过人工确认确实提升时：
```bash
python eval/runner.py --suite knowledge_retrieval --save-as-baseline
```

## 添加新评测用例

每次实现新能力后，在对应数据集目录添加用例：
```bash
# 用例文件格式见 eval/datasets/knowledge_retrieval/kr_template.yaml
```
