#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""白盒车道A 解析器 v0（W4 第一段·source-audit-v1 §1.2 L2 工件层）。

输入=源码目录 → 输出=谱图工件三件:
  codegraph.jsonl    符号表+调用边（每条带 file:line+签名哈希;密度律: 只入工件不入账）
  pattern-hits.jsonl GenSift .pattern 命中（L1 入口/L3' 密钥候选的枚举原料,只入工件;
                    命中行原文不入工件——secrets 类防密值外流）
  digest.json        digest 事实一条（符号数/边数/sha256/解析器版本+pattern 翻译诚实账）
                    ——引擎不写账本!总控验收后落 facts(kind=engine-static 子类
                    codegraph-digest),锚边 provenance 用工件 sha256。

GenSift .pattern → Python re 翻译（#15-3 裁决: 方言(b)翻译+fixtures 迁CI）:
  POSIX 括号类按表展开（[:space:] 等八类;混合括号形态 [[:space:](=,] 同样展开）,
  表外类/Python re 编译不过的语法一律跳过并记录——诚实,不猜。

确定性律: 同输入逐字节同输出——文件序/记录序/JSON 键序全部钉死,无时间戳,
无绝对路径,UTF-8+LF。
"""
import argparse
import ast
import hashlib
import json
import os
import re
import sys

PARSER_VERSION = "whitebox-parser/0.1.0"

# GenSift「ts」语言位覆盖 JS 家族（langpacks 口径: ts/js 同枚举面）
LANG_OF_EXT = {
    ".py": "python",
    ".java": "java",
    ".ts": "ts", ".tsx": "ts", ".js": "ts", ".jsx": "ts",
    ".mjs": "ts", ".cjs": "ts",
}

# ---------------------------------------------------------------- ERE 翻译

# 翻译表: 仅收 POSIX 类中可无损映射 Python re 字符类内容的八类。
# 表外类（graph/print/cntrl/punct…）一律跳过并记录——不猜语义。
_POSIX_CLASSES = {
    "space": r" \t\r\n\v\f",
    "alnum": r"0-9A-Za-z",
    "upper": r"A-Z",
    "lower": r"a-z",
    "digit": r"0-9",
    "alpha": r"A-Za-z",
    "xdigit": r"0-9A-Fa-f",
    "blank": r" \t",
}
_POSIX_TOKEN = re.compile(r"\[:([a-z]+):\]")


def translate_ere(ere):
    """GenSift ERE 方言 → Python re。返回 (python_ere, None) 或 (None, reason)。

    诚实律: 三种跳过——表外 POSIX 类/Python re 编译失败/展开后残留 [:..:] token
    （残留=可能静默错译,宁可跳过）。ERE 与 Python re 对 \<标点> 转义语义一致,
    直通即可;\<字母> 类 GNU 扩展若 Python 不认,编译检查自然拦截。
    """
    if not ere or not ere.strip():
        return None, "empty pattern"
    # GNU 词边界转义（\< \>）: Python re 静默读成字面尖括号——语义分叉,显式跳过
    if re.search(r"\\[<>]", ere):
        return None, "GNU word-boundary escape (\\< or \\>) not representable in Python re"
    for m in _POSIX_TOKEN.finditer(ere):
        if m.group(1) not in _POSIX_CLASSES:
            return None, "POSIX class %s not in translation table" % m.group(0)
    out = _POSIX_TOKEN.sub(lambda m: _POSIX_CLASSES[m.group(1)], ere)
    # ERE 单字符括号类 [[] = 字面左中括号;Python re 同语义但 FutureWarning 且未来
    # 版本可能拒收——机械归一为 \\[（等价、无警告、语义不猜）
    out = out.replace("[[]", "\\[")
    if _POSIX_TOKEN.search(out):
        return None, "residual POSIX class token after translation"
    try:
        re.compile(out)
    except re.error as exc:
        return None, "python re compile failed: %s" % exc
    return out, None


def load_pattern_file(path):
    """解析 .pattern 文件: # 头部键值 + #--- 分隔 + TSV(pattern_id/ere/note...)。"""
    header, rows = {}, []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#---"):
                continue
            if line.startswith("#"):
                m = re.match(r"#\s*(\w+):\s*(.*)", line)
                if m:
                    header[m.group(1)] = m.group(2).strip()
                continue
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].strip() and not parts[0].startswith("#"):
                if parts[0].strip() == "pattern_id":  # TSV 表头行,非数据行
                    continue
                rows.append((parts[0].strip(), parts[1],
                             "\t".join(parts[2:]) if len(parts) > 2 else ""))
    return {"path": path, "filename": os.path.basename(path),
            "class": header.get("class", ""), "lang": header.get("lang", ""),
            "role": header.get("role", ""), "band": header.get("band", ""),
            "version": header.get("version", ""), "patterns": rows}


def load_pattern_dir(pattern_dir):
    out = []
    for name in sorted(os.listdir(pattern_dir)):
        if name.endswith(".pattern"):
            out.append(load_pattern_file(os.path.join(pattern_dir, name)))
    return out


def translate_pattern_dir(pattern_dir):
    """目录级翻译: 返回 (compiled, skipped)——每行要么成要么带理由跳过,无第三态。"""
    compiled, skipped = [], []
    for pf in load_pattern_dir(pattern_dir):
        for pid, ere, _note in pf["patterns"]:
            py, reason = translate_ere(ere)
            if py is None:
                skipped.append({"class": pf["class"], "lang": pf["lang"],
                                "pattern_id": pid, "ere": ere, "reason": reason})
            else:
                compiled.append({"class": pf["class"], "lang": pf["lang"],
                                 "pattern_id": pid, "ere": ere, "python_ere": py,
                                 "regex": re.compile(py)})
    compiled.sort(key=lambda c: (c["class"], c["lang"], c["pattern_id"]))
    skipped.sort(key=lambda s: (s["class"], s["lang"], s["pattern_id"]))
    return compiled, skipped


def posix_classes_used(pattern_dir):
    """诚实账: 语料里实际出现的 POSIX 类 token 计数（翻译原料披露）。"""
    used = {}
    for pf in load_pattern_dir(pattern_dir):
        for _pid, ere, _note in pf["patterns"]:
            for m in _POSIX_TOKEN.finditer(ere):
                used[m.group(0)] = used.get(m.group(0), 0) + 1
    return dict(sorted(used.items()))


def scan_lines(rel_path, lines, compiled_pats):
    """行级扫描（grep -E 同语义: 每行独立 search）。命中行原文不入返回值。"""
    hits = []
    for pat in compiled_pats:
        rx = pat["regex"]
        for i, line in enumerate(lines, 1):
            if rx.search(line):
                hits.append({"class": pat["class"], "lang": pat["lang"],
                             "pattern_id": pat["pattern_id"],
                             "file": rel_path, "line": i})
    return hits


def enum_fixture_langs(enum_root):
    """yield (class, lang): fixtures/enum 下带 manifest.tsv 的目录（测试对账用）。"""
    for cls in sorted(os.listdir(enum_root)):
        cdir = os.path.join(enum_root, cls)
        if not os.path.isdir(cdir):
            continue
        for lang in sorted(os.listdir(cdir)):
            if os.path.isfile(os.path.join(cdir, lang, "manifest.tsv")):
                yield cls, lang


# ---------------------------------------------------------------- 符号/调用

_CALL_KEYWORDS = {
    "if", "for", "while", "switch", "catch", "return", "new", "super",
    "this", "throw", "throws", "else", "do", "try", "synchronized",
    "function", "await", "async", "yield", "import", "package", "export",
    "typeof", "in", "of", "as", "constructor", "elif", "lambda", "print",
}


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _py_signature(node):
    args = [a.arg for a in getattr(node.args, "posonlyargs", []) + node.args.args]
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    kw = [a.arg for a in node.args.kwonlyargs]
    args.extend(kw)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return "%s(%s)" % (node.name, ", ".join(args))


def _parse_python(rel, text, symbols, calls):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False

    def emit_symbol(node, qualname, kind):
        sig = _py_signature(node) if kind != "class" else "%s()" % node.name
        symbols.append({"record": "symbol", "lang": "python", "file": rel,
                        "line": node.lineno, "kind": kind, "name": node.name,
                        "qualname": qualname, "signature": sig,
                        "sig_sha256": _sha(sig)})

    def walk_body(body, prefix, caller):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = "%s.%s" % (prefix, node.name) if prefix else node.name
                emit_symbol(node, qual, "method" if prefix else "function")
                walk_body(node.body, qual, qual)
            elif isinstance(node, ast.ClassDef):
                qual = "%s.%s" % (prefix, node.name) if prefix else node.name
                emit_symbol(node, qual, "class")
                walk_body(node.body, qual, caller)
            else:
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        func = sub.func
                        if isinstance(func, ast.Name):
                            callee = func.id
                        elif isinstance(func, ast.Attribute):
                            callee = func.attr
                        else:
                            continue
                        argc = len(sub.args) + len(sub.keywords)
                        calls.append({"record": "call", "lang": "python",
                                      "file": rel, "line": sub.lineno,
                                      "caller": caller, "callee": callee,
                                      "argc": argc,
                                      "sig_sha256": _sha("%s(%d)" % (callee, argc))})

    walk_body(tree.body, "", "<module>")
    return True


_JAVA_CLASS_RE = re.compile(
    r"^\s*(?:(?:public|private|protected|final|abstract|static|strictfp)\s+)*"
    r"(?:class|interface|enum|record)\s+(\w+)")
_JAVA_METHOD_RE = re.compile(
    r"^\s*(?:(?:public|private|protected|static|final|abstract|synchronized|"
    r"native|default)\s+)*(?:<[^>]+>\s+)?(?:[\w.\[\]<>, ?]*?\s+)?"
    r"(\w+)\s*\(([^()]*)\)\s*(?:throws [\w., ]+)?\s*\{")
_TS_FUNC_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*"
    r"(\w+)\s*\(([^()]*)\)")
_TS_ARROW_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::\s*[^=]+)?="
    r"\s*(?:async\s*)?(?:\(([^()]*)\)|(\w+))\s*=>")
_TS_CLASS_RE = re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)")
_TS_METHOD_RE = re.compile(
    r"^\s*(?:(?:public|private|protected|static|readonly|override|async|"
    r"abstract)\s+)*(?:\*\s*)?(\w+)\s*\(([^()]*)\)\s*(?::\s*[^{;]+)?\s*\{")
_CALL_RE = re.compile(r"(?:\.|\b)([A-Za-z_]\w*)\s*\(")


def _norm_params(raw):
    return ", ".join(p.strip() for p in raw.split(",") if p.strip())


def _line_scan(rel, lines, lang, symbols, calls, decl_res, class_res):
    """Java/TS 行级抽取: 声明行建符号并推进 caller 上下文;非声明行抽调用边。"""
    current_class = None
    current_method = None
    for i, line in enumerate(lines, 1):
        is_decl = False
        m = class_res.match(line)
        if m:
            current_class, current_method = m.group(1), None
            kind = "class" if lang == "java" else "class"
            sig = "%s()" % current_class
            symbols.append({"record": "symbol", "lang": lang, "file": rel,
                            "line": i, "kind": kind, "name": current_class,
                            "qualname": current_class, "signature": sig,
                            "sig_sha256": _sha(sig)})
            is_decl = True
        for dre in decl_res:
            m = dre.match(line)
            if not m:
                continue
            name, params = m.group(1), m.group(2)
            if name in _CALL_KEYWORDS or name.startswith("_") and lang == "ts":
                continue
            qual = "%s.%s" % (current_class, name) if current_class else name
            if lang == "java" and current_class and name == current_class:
                current_method = name  # 构造器: 推进 caller 上下文但不建符号
                is_decl = True
                break
            kind = "method" if current_class else "function"
            sig = "%s(%s)" % (name, _norm_params(params))
            symbols.append({"record": "symbol", "lang": lang, "file": rel,
                            "line": i, "kind": kind, "name": name,
                            "qualname": qual, "signature": sig,
                            "sig_sha256": _sha(sig)})
            current_method = name
            is_decl = True
            break
        if is_decl or line.lstrip().startswith(("//", "*", "/*", "#")):
            continue
        for m in _CALL_RE.finditer(line):
            callee = m.group(1)
            if callee in _CALL_KEYWORDS:
                continue
            if current_class and current_method:
                caller = "%s.%s" % (current_class, current_method)
            elif current_method:
                caller = current_method
            elif current_class:
                caller = current_class
            else:
                caller = "<module>"
            argc = _count_args(line, m.end())
            calls.append({"record": "call", "lang": lang, "file": rel,
                          "line": i, "caller": caller, "callee": callee,
                          "argc": argc,
                          "sig_sha256": _sha("%s(%d)" % (callee, argc))})


def _count_args(line, start):
    """从调用左括号后数顶层逗号→argc（近似值,v0 行级口径,确定性优先）。"""
    depth, commas, seen = 0, 0, False
    for ch in line[start - 1:]:
        if ch == "(":
            depth += 1
            seen = True
        elif ch == ")":
            depth -= 1
            if seen and depth == 0:
                break
        elif ch == "," and depth == 1:
            commas += 1
    if not seen:
        return 0
    body = line[start - 1:]
    inner = body[1:body.find(")")] if ")" in body else body[1:]
    return 0 if not inner.strip() else commas + 1


def _resolve_callees(symbols, calls):
    """同名唯一符号名→callee_symbol 回填（解析不了的留 null,诚实不猜）。"""
    by_lang_name = {}
    for s in symbols:
        by_lang_name.setdefault((s["lang"], s["name"]), set()).add(s["qualname"])
    for c in calls:
        quals = by_lang_name.get((c["lang"], c["callee"]))
        c["callee_symbol"] = sorted(quals)[0] if quals and len(quals) == 1 else None


def analyze(source_dir, compiled):
    """源码目录→(symbols, calls, hits, file_stats, unparsed)。文件序=相对路径字典序钉死。"""
    symbols, calls, hits = [], [], []
    files_by_lang = {"python": 0, "java": 0, "ts": 0}
    unparsed = 0
    rel_files = []
    for root, dirs, names in os.walk(source_dir):
        dirs.sort()
        for name in sorted(names):
            full = os.path.join(root, name)
            rel = "/".join(os.path.relpath(full, source_dir).split(os.sep))
            lang = LANG_OF_EXT.get(os.path.splitext(name)[1].lower())
            if lang:
                rel_files.append((rel, full, lang))
                files_by_lang[lang] += 1
    rel_files.sort()
    pats_by_lang = {}
    for p in compiled:
        pats_by_lang.setdefault(p["lang"], []).append(p)
    for rel, full, lang in rel_files:
        with open(full, "rb") as f:
            text = f.read().decode("utf-8", errors="replace")
        lines = text.splitlines()
        hits.extend(scan_lines(rel, lines, pats_by_lang.get(lang, [])))
        if lang == "python":
            if not _parse_python(rel, text, symbols, calls):
                unparsed += 1
        elif lang == "java":
            _line_scan(rel, lines, "java", symbols, calls,
                       [_JAVA_METHOD_RE], _JAVA_CLASS_RE)
        else:
            _line_scan(rel, lines, "ts", symbols, calls,
                       [_TS_FUNC_RE, _TS_METHOD_RE, _TS_ARROW_RE], _TS_CLASS_RE)
    _resolve_callees(symbols, calls)
    symbols.sort(key=lambda s: (s["file"], s["line"], s["qualname"]))
    calls.sort(key=lambda c: (c["file"], c["line"], c["caller"], c["callee"]))
    hits.sort(key=lambda h: (h["class"], h["lang"], h["pattern_id"],
                             h["file"], h["line"]))
    stats = {"total": len(rel_files), "python": files_by_lang["python"],
             "java": files_by_lang["java"], "ts": files_by_lang["ts"]}
    return symbols, calls, hits, stats, unparsed


# ---------------------------------------------------------------- 工件写出


def _jsonl(records):
    return "".join(json.dumps(r, sort_keys=True, ensure_ascii=False,
                              separators=(",", ":")) + "\n" for r in records)


def _write(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def run(source_dir, out_dir, patterns_dir):
    """全流程: 翻译→解析→扫描→工件落盘。引擎不写账本（出目录仅三件工件）。"""
    compiled, skipped = translate_pattern_dir(patterns_dir)
    rows = sum(len(pf["patterns"]) for pf in load_pattern_dir(patterns_dir))
    symbols, calls, hits, stats, unparsed = analyze(source_dir, compiled)
    graph_records = symbols + calls  # 先符号后调用;各自内部已钉死排序
    graph_bytes = _jsonl(graph_records)
    hits_bytes = _jsonl(hits)
    os.makedirs(out_dir, exist_ok=True)
    _write(os.path.join(out_dir, "codegraph.jsonl"), graph_bytes)
    _write(os.path.join(out_dir, "pattern-hits.jsonl"), hits_bytes)
    digest = {
        "kind": "codegraph-digest",
        "parser_version": PARSER_VERSION,
        "files": stats,
        "unparsed_files": unparsed,
        "symbol_count": len(symbols),
        "edge_count": len(calls),
        "codegraph_sha256": hashlib.sha256(graph_bytes.encode("utf-8")).hexdigest(),
        "pattern_hits_count": len(hits),
        "pattern_hits_sha256": hashlib.sha256(hits_bytes.encode("utf-8")).hexdigest(),
        "patterns": {
            "files": len(load_pattern_dir(patterns_dir)),
            "rows": rows,
            "translated": len(compiled),
            "skipped": skipped,
            "posix_classes_used": posix_classes_used(patterns_dir),
        },
    }
    _write(os.path.join(out_dir, "digest.json"),
           json.dumps(digest, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")))
    return digest


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    default_patterns = os.path.join(here, "..", "..", "knowledge", "staging",
                                    "gensift-intake", "classes", "patterns")
    ap = argparse.ArgumentParser(description="白盒车道A 解析器 v0（确定性,不写账本）")
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--patterns-dir", default=default_patterns)
    args = ap.parse_args(argv)
    if not os.path.isdir(args.source_dir):
        sys.stderr.write("source-dir 不存在: %s\n" % args.source_dir)
        return 2
    if not os.path.isdir(args.patterns_dir):
        sys.stderr.write("patterns-dir 不存在: %s\n" % args.patterns_dir)
        return 2
    digest = run(args.source_dir, args.out_dir, args.patterns_dir)
    sys.stdout.write("%s symbols=%d edges=%d hits=%d translated=%d skipped=%d\n" % (
        digest["parser_version"], digest["symbol_count"], digest["edge_count"],
        digest["pattern_hits_count"], digest["patterns"]["translated"],
        len(digest["patterns"]["skipped"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
