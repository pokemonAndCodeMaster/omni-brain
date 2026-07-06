#!/usr/bin/env python3
"""
compile_index.py — 知识库索引编译器

从 knowledge/ 目录的所有 Markdown 文件重建所有派生索引：
  1. SQLite FTS5 BM25 全文索引（.derived/fts.db）
  2. 关系图（.derived/graph.json）
  3. 统计缓存（.derived/stats.json）
  4. CodeModule 卡片的 code_hash 更新

用法：
    python scripts/compile_index.py              # 全量重建
    python scripts/compile_index.py --incremental # 仅更新变更文件（未实现，待 Phase 2）
    python scripts/compile_index.py --code-hash   # 仅更新代码哈希

设计原则：
    - .derived/ 下的所有产物是可重建的派生产物，不提交 git
    - 知识文件（knowledge/*.md）是唯一事实来源
    - 此脚本是幂等的，多次运行结果相同
"""

# TODO (Phase 1): 实现以下功能
# 1. 扫描 knowledge/ 下所有 .md 文件
# 2. 解析 YAML frontmatter（使用 python-frontmatter 库）
# 3. 对正文进行 jieba 分词
# 4. 构建 SQLite FTS5 表并插入索引数据
# 5. 从 relations 字段构建邻接表写入 graph.json
# 6. 统计各 type/domain 的卡片数量写入 stats.json
# 7. 若有 CodeModule 类型，计算关联代码文件的 SHA256 并回写 code_hash

if __name__ == "__main__":
    print("compile_index.py — 待 Phase 1 实现")
    print("计划功能：BM25索引 + 关系图 + 统计 + CodeModule哈希")
