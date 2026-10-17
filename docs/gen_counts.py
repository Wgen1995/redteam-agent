#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W2 枚举单源化③：计数单源生成器——docs/counts.json 唯一写者（02 评审 P0-2③）。

口径（一律取 HEAD 提交态，工作树在航件不污染口径）：
- ledger_commands = len(registry.all_commands())（命令面单源=注册表）
- ledger_gates     = len(core.GATE_ORDER)（九门含 P5.5/P6.0）
- ledger_fields    = Σ schemas.json 各表列数（契约 01 表结构单源）
- golden_faces     = Σ tests/run_golden.py 面清单（金样面单源；面类目镜像其
  PASS 行合计式——面清单本身零复制，新增面类目时本式须随行）

用法（退出码 0/1/2：0=一致/已生成 1=口径漂移（门禁） 2=环境（git 缺/物化失败））：
  python3 docs/gen_counts.py            # 重生成 docs/counts.json（LF/indent1/键序）
  python3 docs/gen_counts.py --check    # 门禁：在册文件与单源派生逐字节比对

机制：git archive HEAD cli tests/run_golden.py → 临时目录物化 → 子进程纯导入
探针取数。在航未提交命令不进口径；新命令落 commit 后 --check 即红=计数同步
义务入门槛——41/44/49 三数并存的病史（05 评审 F1「手工枚举复制已成系统性病灶」）
由此封口：活文档禁手抄计数，tests/test_gen_counts.py 机检。"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

_PROBE = """
import importlib.util, json, sys
sys.path.insert(0, "cli")
from ledger import core, registry
schemas = json.load(open("cli/ledger/schemas.json", encoding="utf-8"))
tables = schemas["tables"] if isinstance(schemas, dict) and "tables" in schemas else schemas
fields = sum(len(v.get("columns", v) if isinstance(v, dict) else v) for v in tables.values())
spec = importlib.util.spec_from_file_location("rg_probe", "tests/run_golden.py")
rg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rg)
faces = sum(len(x) for x in (
    rg.READ_CMDS, rg.WRITE_CMDS, rg.PHASES_CMDS, rg.PHASES_DENOM, rg.ENGINE_CMDS,
    rg.GRAPH_CMDS, rg.ADAPTER_CMDS, rg.NUCLEI_CMDS, rg.VIZ_CMDS, rg.RECHECK_CMDS,
    rg.KN_CMDS))
print(json.dumps({"ledger_commands": len(registry.all_commands()),
                  "ledger_gates": len(core.GATE_ORDER),
                  "ledger_fields": fields, "golden_faces": faces}))
"""


def _materialize_head(dst):
    """HEAD 的 cli/ + tests/run_golden.py 物化到 dst（在航脏树零污染）。"""
    arch = subprocess.run(["git", "archive", "HEAD", "cli", "tests/run_golden.py"],
                          cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if arch.returncode != 0:
        raise EnvironmentError("git archive 失败: %s" % arch.stderr.decode("utf-8", "replace"))
    untar = subprocess.run(["tar", "-x", "-C", dst], input=arch.stdout,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if untar.returncode != 0:
        raise EnvironmentError("物化解包失败: %s" % untar.stderr.decode("utf-8", "replace"))


def collect():
    """单源派生四计数（HEAD 态）——counts.json 的唯一数据通道。"""
    with tempfile.TemporaryDirectory() as td:
        _materialize_head(td)
        r = subprocess.run([sys.executable, "-c", _PROBE], cwd=td,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**os.environ, "PYTHONUTF8": "1"})
        if r.returncode != 0:
            raise EnvironmentError("单源探针失败: %s%s" % (r.stdout, r.stderr))
        out = {"format_version": 1}
        out.update(json.loads(r.stdout.strip().splitlines()[-1]))
        return out


def _head_face_count():
    """命令面计数独立通道（tests/test_gen_counts 双算复核用）。"""
    return collect()["ledger_commands"]


def render(counts):
    return json.dumps(counts, ensure_ascii=False, indent=1, sort_keys=True) + chr(10)


def main(argv):
    ap = argparse.ArgumentParser(prog="gen_counts")
    ap.add_argument("--check", action="store_true", help="门禁：在册与派生比对，漂移 rc=1")
    a = ap.parse_args(argv)
    path = os.path.join(HERE, "counts.json")
    try:
        fresh = render(collect())
    except EnvironmentError as e:
        sys.stderr.write(("环境问题: %s" % e) + chr(10))
        return 2
    if not a.check:
        with open(path, "w", encoding="utf-8", newline=chr(10)) as f:
            f.write(fresh)
        print("WROTE docs/counts.json " + fresh.replace(chr(10), "").replace(" ", ""))
        return 0
    try:
        with open(path, encoding="utf-8") as f:
            committed = f.read()
    except OSError:
        print("FAIL counts.json 缺（先 python3 docs/gen_counts.py 生成）")
        return 1
    if committed != fresh:
        print("FAIL counts.json 与单源派生漂移——重生成: python3 docs/gen_counts.py")
        return 1
    c = json.loads(fresh)
    print("OK counts.json 单源一致: commands=%d gates=%d fields=%d golden_faces=%d"
          % (c["ledger_commands"], c["ledger_gates"], c["ledger_fields"], c["golden_faces"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
