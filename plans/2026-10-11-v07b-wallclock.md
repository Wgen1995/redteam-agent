# v0.7b wall_clock 双轨（2026-10-11）

## 问题
- timeline 用场景钟（battle 内单调），真实墙钟只在 runner 侧 TSV——**账本内看不出断连窗口**（b31-34 API 断连 2h、b30 重启 7h 均靠人工对表才发现）。

## 设计（轻量：事件轨，零 schema 迁移）
1. `cli/ledger/wallclock.py`：
   - `mint_wall_sync(goal_dir, phase, note="")` → 追加事件 `clock-sync wall=<ISO8601> phase=<p> note=<n>`（走 core.append 落哈希链）。
   - `detect_gaps(rows, min_sec=900)` 纯函数：相邻 wall-sync 的墙差 > min_sec → 返回 [(ts, gap_sec)]，供 settle/审计报「断连嫌疑窗口」。
2. battle.py 在 init/launch/DONE 结算前各铸一枚（3 行接线）。
3. 不动场景钟、不动既有事件、旧账本零影响（无 clock-sync 行=detect_gaps 空）。

## 验收
- 新测 test_v07b_wallclock：铸造格式/空轨容错/gap 检出（含跨午夜）三面。
- 全套件 RC=0。
