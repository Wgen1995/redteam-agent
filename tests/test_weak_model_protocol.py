# -*- coding: utf-8 -*-
"""M08 弱模型档协议可检测（批次 6 T2）——缺命令步骤的「终止报告」形态可检测。

纯函数定义于测试模块（eval 专用，不入 CLI 面——铁律 7）；
规则=存在以 `- cmd:` 起行或 \`\`\`bash 围栏内的行且含 tanyin- 前缀命令。"""
import os, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(HERE, "evals", "samples", "p4-no-command.md")
FENCE = "\`\`\`"  # 三个反引号（避模板/转义歧义，单源）


def has_executable_command(duty_lines):
    in_fence = False
    for ln in duty_lines:
        s = ln.strip()
        if s.startswith(FENCE + "bash"):
            in_fence = True
            continue
        if s.startswith(FENCE) and in_fence:
            in_fence = False
            continue
        if (s.startswith("- cmd:") or in_fence) and "tanyin-" in s:
            return True
    return False


class TestWeakModelProtocol(unittest.TestCase):
    def test_normal_step_has_command(self):
        lines = ["## P4 差分步", "- duty: 对目标执行认证后差分",
                 "- cmd: tanyin-ledger validate --goal-dir .", "- exit: 差分完成"]
        self.assertTrue(has_executable_command(lines))
    def test_normal_step_bash_fence(self):
        lines = ["- duty: 跑校验", FENCE + "bash", "tanyin-ledger validate --goal-dir .", FENCE]
        self.assertTrue(has_executable_command(lines))
    def test_fence_without_tanyin_is_not_command(self):
        lines = ["- duty: 散文", FENCE + "bash", "make build", FENCE]
        self.assertFalse(has_executable_command(lines))
    def test_sample_step_without_command(self):
        with open(SAMPLE, encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertFalse(has_executable_command(lines))
    def test_terminated_report_detectable(self):
        with open(SAMPLE, encoding="utf-8") as f:
            lines = f.read().splitlines()
        terminated = not has_executable_command(lines)  # 总控消费端：False 步=终止报告
        self.assertTrue(terminated)  # 判定「未给出命令的步骤终止报告」可检测


if __name__ == "__main__":
    unittest.main()
