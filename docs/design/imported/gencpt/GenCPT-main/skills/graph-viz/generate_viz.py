#!/usr/bin/env python3
"""
GenCPT Knowledge Graph Visualizer Generator

从 GenCPT 会话目录的 knowledge_graph/ 子目录读取所有节点和边 JSON，
生成交互式 HTML 可视化文件。

用法:
  python3 generate_viz.py --session-dir /tmp/gencpt-xxx [--output path] [--offline]
  python3 generate_viz.py -s /tmp/gencpt-xxx -o viz.html --offline

参数:
  --session-dir, -s   GenCPT 会话目录路径（包含 knowledge_graph/ 子目录）  [必填]
  --output, -o        输出 HTML 文件路径                                    [默认: {session-dir}/knowledge_graph_viz.html]
  --offline           离线模式：内嵌 cytoscape.min.js（文件约 500KB）
  --online            在线模式：使用 CDN 加载 cytoscape（默认，文件约 155KB）
  --title, -t         HTML 页面标题                                          [默认: 自动从 session_config 生成]

示例:
  # 在线模式（默认）
  python3 generate_viz.py -s /tmp/gencpt-k3s-20260722-100843

  # 离线模式（可发给别人，无需联网）
  python3 generate_viz.py -s /tmp/gencpt-k3s-20260722-100843 --offline -o report_viz.html

  # Pipeline 完成后自动调用（在 SKILL.md 中）
  python3 {套件根}/skills/graph-viz/generate_viz.py -s {session_dir} --offline
"""

import argparse
import json
import os
import re
import sys
import urllib.request

# ====== 常量 ======
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_V1 = os.path.join(SCRIPT_DIR, "template.html")           # V1 无旋转
TEMPLATE_V1_1 = os.path.join(SCRIPT_DIR, "template_v1.1.html")    # V1.1 带旋转
CYTOSCAPE_CDN = "https://unpkg.com/cytoscape@3.30.2/dist/cytoscape.min.js"
CYTOSCAPE_CDN_TAG = f'<script src="{CYTOSCAPE_CDN}"></script>'


def fix_json_syntax(content):
    """修复常见的 JSON 语法错误：
    - 数组元素之间缺少逗号（} 和 { 之间）
    """
    # 修复数组中 } \n { 之间缺少逗号的情况
    # 匹配：} 后面紧跟换行和空格然后是 { （但在数组上下文中）
    fixed = re.sub(r'}\s*\n\s*\{', '},\n{', content)
    return fixed


def read_json_file(filepath):
    """读取 JSON 文件，自动修复常见语法错误"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 尝试直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # 修复并重试
        fixed = fix_json_syntax(content)
        try:
            data = json.loads(fixed)
            print(f"  [WARN] {os.path.basename(filepath)}: 自动修复 JSON 语法 ({e.msg} at line {e.lineno})")
            return data
        except json.JSONDecodeError as e2:
            print(f"  [ERROR] {os.path.basename(filepath)}: JSON 解析失败 - {e2.msg} at line {e2.lineno}")
            print(f"  [ERROR] 请手动检查文件: {filepath}")
            return None


def read_and_merge(session_dir):
    """读取会话目录中 knowledge_graph/ 下的所有 JSON 文件并合并"""
    kg_dir = os.path.join(session_dir, "knowledge_graph")
    if not os.path.isdir(kg_dir):
        print(f"[ERROR] 知识图谱目录不存在: {kg_dir}")
        sys.exit(1)

    nodes_dir = os.path.join(kg_dir, "nodes")
    edges_dir = os.path.join(kg_dir, "edges")

    # 读取所有节点（去重：同 ID 的节点只保留第一个）
    nodes = []
    seen_ids = set()
    if os.path.isdir(nodes_dir):
        for fname in sorted(os.listdir(nodes_dir)):
            if not fname.endswith('.json'):
                continue
            fpath = os.path.join(nodes_dir, fname)
            data = read_json_file(fpath)
            if data is None:
                print(f"  [SKIP] 跳过文件: {fname}")
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                nid = item.get('id', '')
                if nid and nid not in seen_ids:
                    seen_ids.add(nid)
                    nodes.append(item)
                elif nid:
                    # 重复节点，跳过（findings.json 和 findings_k8s.json 可能有重复）
                    pass

    # 读取所有边（去重：同 from+to+edge_type+atk_cand 的边只保留第一个）
    # 注意：attack_verify 边可能有多条指向同一 attack（不同 ATK-CAND，不同 Phase），不能只按 from+to+type 去重
    edges = []
    seen_edges = set()
    if os.path.isdir(edges_dir):
        for fname in sorted(os.listdir(edges_dir)):
            if not fname.endswith('.json'):
                continue
            fpath = os.path.join(edges_dir, fname)
            data = read_json_file(fpath)
            if data is None:
                print(f"  [SKIP] 跳过文件: {fname}")
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                # 去重 key：from + to + edge_type + atk_cand（如有）
                atk_cand = item.get('attrs', {}).get('atk_cand', '')
                eid = (item.get('from_node', ''), item.get('to_node', ''), item.get('edge_type', ''), atk_cand)
                if eid not in seen_edges:
                    seen_edges.add(eid)
                    edges.append(item)

    # 读取 progress.json
    progress = {}
    progress_path = os.path.join(session_dir, "progress.json")
    if os.path.isfile(progress_path):
        progress = read_json_file(progress_path) or {}

    # 读取 session_config.json
    session_config = {}
    config_path = os.path.join(session_dir, "session_config.json")
    if os.path.isfile(config_path):
        session_config = read_json_file(config_path) or {}

    # 构建图谱数据
    graph = {
        "nodes": nodes,
        "edges": edges,
        "progress": progress,
        "session_config": session_config,
    }

    return graph


def download_cytoscape():
    """下载 cytoscape.min.js 用于离线模式"""
    print(f"[INFO] 下载 cytoscape.js (离线模式)...")
    try:
        req = urllib.request.Request(CYTOSCAPE_CDN, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            js_content = resp.read().decode('utf-8')
        print(f"[INFO] 下载完成: {len(js_content)} bytes")
        return js_content
    except Exception as e:
        print(f"[WARN] 下载失败: {e}")
        print(f"[WARN] 回退到在线模式 (CDN)")
        return None


def generate(session_dir, output, offline, title=None, template_file=None):
    """生成可视化 HTML 文件"""
    print(f"[INFO] 会话目录: {session_dir}")

    # 1. 读取并合并数据
    print(f"[INFO] 读取知识图谱数据...")
    graph_data = read_and_merge(session_dir)
    node_count = len(graph_data["nodes"])
    edge_count = len(graph_data["edges"])
    print(f"[INFO] 节点: {node_count}, 边: {edge_count}")

    if node_count == 0:
        print("[ERROR] 无节点数据，无法生成可视化")
        sys.exit(1)

    # 2. 读取模板（默认 V1.1 带旋转）
    if template_file is None:
        template_file = TEMPLATE_V1_1
    if not os.path.isfile(template_file):
        print(f"[ERROR] 模板文件不存在: {template_file}")
        sys.exit(1)
    with open(template_file, 'r', encoding='utf-8') as f:
        template = f.read()

    # 3. 注入数据
    data_js = "const graphData = " + json.dumps(graph_data, ensure_ascii=False) + ";"
    html = template.replace("__GRAPH_DATA__", data_js)

    # 4. 处理 cytoscape 库（在线/离线）
    if offline:
        js_content = download_cytoscape()
        if js_content:
            lib_tag = f'<script>\n{js_content}\n</script>'
        else:
            lib_tag = CYTOSCAPE_CDN_TAG
    else:
        lib_tag = CYTOSCAPE_CDN_TAG

    html = html.replace("__CYTOSCAPE_LIB__", lib_tag)

    # 5. 设置标题
    if title:
        html = html.replace(
            "<title>GenCPT 知识图谱可视化 — k3s-20260722-100843</title>",
            f"<title>{title}</title>"
        )
    else:
        # 自动从 session_config 生成标题
        sc = graph_data.get("session_config", {})
        session_id = sc.get("session_id", "unknown")
        default_title = f"GenCPT 知识图谱可视化 — {session_id}"
        html = html.replace(
            "<title>GenCPT 知识图谱可视化 — k3s-20260722-100843</title>",
            f"<title>{default_title}</title>"
        )

    # 6. 写入输出文件
    with open(output, 'w', encoding='utf-8') as f:
        f.write(html)

    file_size = os.path.getsize(output)
    mode_label = "离线" if (offline and '__CYTOSCAPE_LIB__' not in html) else "在线"
    print(f"[OK] 生成完成: {output}")
    print(f"     模式: {mode_label}")
    print(f"     大小: {file_size / 1024:.0f} KB")
    print(f"     节点: {node_count} / 边: {edge_count}")
    if mode_label == "离线":
        print(f"     可离线使用（无需联网）")
    else:
        print(f"     需要联网加载 cytoscape.js CDN")


def main():
    parser = argparse.ArgumentParser(
        description="GenCPT 知识图谱可视化生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -s /tmp/gencpt-k3s-20260722-100843
  %(prog)s -s /tmp/gencpt-k3s-20260722-100843 --offline -o report.html
  %(prog)s -s /tmp/gencpt-k3s-20260722-100843 --online -t "渗透测试报告可视化"
        """
    )
    parser.add_argument(
        "--session-dir", "-s",
        required=True,
        help="GenCPT 会话目录路径（包含 knowledge_graph/ 子目录）"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出 HTML 文件路径（默认: {session-dir}/knowledge_graph_viz.html）"
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--offline",
        action="store_true",
        help="离线模式：内嵌 cytoscape.min.js（文件约 500KB，可离线使用）"
    )
    mode_group.add_argument(
        "--online",
        action="store_true",
        help="在线模式：使用 CDN 加载 cytoscape（默认，文件约 155KB）"
    )
    parser.add_argument(
        "--title", "-t",
        default=None,
        help="HTML 页面标题（默认自动生成）"
    )
    template_group = parser.add_mutually_exclusive_group()
    template_group.add_argument(
        "--rotate",
        action="store_true",
        default=True,
        help="使用 V1.1 模板（带星云旋转，默认）"
    )
    template_group.add_argument(
        "--no-rotate",
        action="store_true",
        help="使用 V1 模板（不带旋转）"
    )

    args = parser.parse_args()

    # 验证会话目录
    session_dir = os.path.abspath(args.session_dir)
    if not os.path.isdir(session_dir):
        print(f"[ERROR] 会话目录不存在: {session_dir}")
        sys.exit(1)

    # 确定输出路径
    if args.output:
        output = os.path.abspath(args.output)
    else:
        output = os.path.join(session_dir, "knowledge_graph_viz.html")

    # 确定模式（默认在线）
    offline = args.offline

    # 确定模板（默认 V1.1 带旋转）
    template_file = TEMPLATE_V1 if args.no_rotate else TEMPLATE_V1_1

    generate(session_dir, output, offline, args.title, template_file)


if __name__ == "__main__":
    main()
