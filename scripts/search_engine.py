#!/usr/bin/env python3
"""
search_engine.py — 知识库多路检索引擎

执行「意图路由 → 范围过滤 → BM25检索 → 关系图扩展 → 重排序 → 分级输出」流水线。

用法：
    python scripts/search_engine.py "FastAPI 异步连接池管理"
    python scripts/search_engine.py "Raft 选举" --domain distributed_systems
    python scripts/search_engine.py "lifespan 配置" --type Norm,Pitfall
    python scripts/search_engine.py "代码架构" --domain meta --top-k 15

输出格式（JSON）：
    {
      "query": "...",
      "full_read": [{"path": "...", "title": "...", "score": 0.9, "type": "Pitfall"}],
      "summary_only": [{"path": "...", "title": "...", "description": "..."}],
      "title_only": [{"path": "...", "title": "..."}],
      "stats": {"total_candidates": N, "latency_ms": M}
    }

设计原则：
    - BM25 通过 SQLite FTS5 实现，零额外依赖
    - 关系图从 .derived/graph.json 加载（由 compile_index.py 生成）
    - 图扩展有硬上限（top_k * 3），防止无限扩散
    - Norm 和 Pitfall 类型强制进入 full_read
"""

# TODO (Phase 2): 实现以下功能
# 1. 意图路由：判断查询类型（精确查找/探索/操作指南/代码定位）
# 2. 范围过滤：解析 --domain / --type 参数，生成 SQL WHERE 子句
# 3. BM25 检索：对 jieba 分词后的查询在 FTS5 表上执行检索
# 4. 关系图扩展：BM25 Top-K 结果沿 graph.json 扩展 1-2 跳
# 5. 重排序：综合 BM25 分、关系强度、新鲜度
# 6. 分级输出：Norm/Pitfall → full_read；中分 → summary_only；低分 → title_only

if __name__ == "__main__":
    print("search_engine.py — 待 Phase 2 实现")
    print("计划功能：意图路由 + BM25 + 图扩展 + 重排序 + 分级输出")
