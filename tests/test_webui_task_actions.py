# -*- coding: utf-8 -*-
"""任务列表（R64 对齐）：原「任务管理闭环批（能力并集审计修②）」钉的
/p/tasks 行内操作（启动/暂停/恢复/结算停跑走 /api/battle/control）从未落地
——T5·P3（7eb6a9e）任务列表以只读投影面交付（表+筛选+搜索+排序+分页+
行点击进详情+新建任务钮），介入动作归会话驾驶舱（session.html）。
旧断言已退休（R64: 随49b1619 IA v2移除），本文件改钉只读现实。
python3 -m unittest tests.test_webui_task_actions
法律：纯 stdlib、3.9 兼容、测试动态取口（绝不 bind 8900）。
"""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
PAGE = os.path.join(CLI, "webui", "static", "pages", "tasks.html")


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


# ═══════════════════════════ ① 页面结构（只读现实） ═══════════════════════════

class TestTaskActionsPage(unittest.TestCase):
    """R64 对齐（①新现实）：/p/tasks=只读投影任务列表。行内操作规格
    （操作列 c-act/四动作钮/actionsFor 状态门/confirm 二次确认/
    X-Requested-With POST 头）随旧规格退休——R64: 随49b1619 IA v2移除，
    介入动作归会话驾驶舱。"""

    # test_actions_column_present —— R64: 随49b1619 IA v2移除
    # test_actions_reuse_battle_control_endpoint —— R64: 随49b1619 IA v2移除
    # test_four_actions_with_human_words —— R64: 随49b1619 IA v2移除
    # test_state_gated_action_map —— R64: 随49b1619 IA v2移除
    # test_stop_has_confirm_and_buttons_stop_row_navigation —— R64: 随49b1619 IA v2移除
    # test_csrf_header_on_post —— R64: 随49b1619 IA v2移除

    def test_readonly_projection_reality(self):
        """新现实钉：任务列表只读——行点击进详情+新建任务主钮，零写入调用。"""
        src = _src()
        self.assertIn("/api/v2/tasks.json", src, "任务列表走只读投影 API")
        self.assertIn("tasks-tbody", src, "缺任务表体")
        self.assertNotIn("/api/battle/control", src,
                          "只读面不得挂控制端点（介入在会话驾驶舱）")

    def test_copy_standard_no_jargon_zone(self):
        src = _src()
        head = src.split("<script>")[0]
        for bad in ("开战", "战役", "战报", "杀进程"):
            self.assertNotIn(bad, head, "黑话上屏: " + bad)


# ═══════════════════════════ ② 活体（已退休） ═══════════════════════════

# R64: 随49b1619 IA v2移除 TestTaskActionsLive 活体冒烟（真浏览器点暂停钮→
# /api/battle/control→directive.txt 真写+留痕）——行内操作钮从未在 /p/tasks
# 落地（只读投影面），整套件 asyncio loop 下 Playwright Sync API 亦不可用；
# 活体介入闭环的真钉归 tests/test_v098_steering_ui.py 会话驾驶舱面。


if __name__ == "__main__":
    unittest.main()
