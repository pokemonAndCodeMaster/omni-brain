#!/usr/bin/env python3
"""
ingest_pipeline.py — 知识摄入流水线

执行「保存原料 → 分块 → 草案 → 验证门禁 → 冲突检测 → 审核 → 入库 → 重编译」。
这是知识库信息无损保障的核心脚本。

用法：
    python scripts/ingest_pipeline.py --file raw/articles/example.md
    python scripts/ingest_pipeline.py --text "直接输入文本内容" --source-type manual
    python scripts/ingest_pipeline.py --conversation raw/conversations/session_001.md

关键设计：
    - 验证门禁（Verification Gate）：草案不完整则打回，不入库
    - 变更提案：冲突内容不直接覆盖，生成提案等待确认
    - 幂等性：相同内容多次摄入，结果一致（重复检测）
"""

# TODO (Phase 1): 实现以下功能
# 1. 原料保存：将输入内容保存到 raw/（不可变）
# 2. 分块：按语义边界（标题/段落）分块，chunk_size 见 config/system.yaml
# 3. 草案生成：调用 LLM 为每个分块生成卡片草案（含 Frontmatter）
# 4. 摄入清单输出：让用户确认识别到的知识点列表
# 5. 验证门禁：对照清单检查草案完整性，不通过则打回
# 6. 冲突检测：调用 search_engine.py 比对现有卡片
# 7. 审核流程：冲突情况暂停等待确认，无冲突自动继续
# 8. 入库：写入对应目录，更新 index.md 和 log.md
# 9. 重编译：调用 compile_index.py

if __name__ == "__main__":
    print("ingest_pipeline.py — 待 Phase 1 实现")
    print("计划功能：分块→草案→验证门禁→冲突检测→入库→重编译")
