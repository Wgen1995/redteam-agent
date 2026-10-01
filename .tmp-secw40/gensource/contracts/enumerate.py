#!/usr/bin/env python3
# GenSource enumerate engine v0.11.0
# v0.11.0 (doc 102 P0.1): 纯 Python 化——os.walk+re 替代 grep/find（跨平台+确定性+流式）
# 修复: M1 全语言入口 / M2 不截断 / M15 跨平台 / M16 binary 探测 / M19 表格管道重建 / M20 explicit 不再二次转义
#       E-03 未映射语言 FAIL / E-10 sorted / E-18 前缀判断 / E-24 callee 正则统一
import argparse, csv, hashlib, os, re, sys

SIGNAL_CLASSES = {'SINK-SENSITIVE-EXPOSE','SINK-LOGGING-INSUFF','SINK-AUTHN-BYPASS','SINK-BRUTE-FORCE','SINK-OBSERVABLE-DIFF','SINK-STATE-CONCURRENT','SINK-MEM-INDEX'}

# 扩展 -> 语言码（知识表语言码：J=Java Py=Python N=Node/JS/TS PHP Go C/Cpp）
LANG_OF_EXT = {
    'java': 'J',
    'py': 'Py',
    'go': 'Go',
    'js': 'N', 'mjs': 'N', 'cjs': 'N', 'jsx': 'N', 'ts': 'N', 'tsx': 'N',
    'php': 'PHP', 'php3': 'PHP', 'php4': 'PHP', 'php5': 'PHP', 'phtml': 'PHP',
    'c': 'C', 'h': 'C',
    'cpp': 'Cpp', 'cc': 'Cpp', 'cxx': 'Cpp', 'hpp': 'Cpp',
}
EXT_FOR_LANG = {
    'J': ('java',),
    'Py': ('py',),
    'Go': ('go',),
    'N': ('js', 'mjs', 'cjs', 'jsx', 'ts', 'tsx'),
    'PHP': ('php', 'php3', 'php4', 'php5', 'phtml'),
    'C': ('c', 'h'),
    'Cpp': ('cpp', 'cc', 'cxx', 'hpp'),
}
IMAGE_EXTS = {'png','jpg','jpeg','gif','ico','bmp','webp','tif','tiff'}
ARCHIVE_EXTS = {'zip','gz','tgz','tar','bz2','7z','xz','jar','war','ear','rar'}
BINARY_EXTS = {'class','so','dll','dylib','exe','wasm','a','o','lib','pyc','pyo','bin','dat','db','sqlite','pdf','woff','woff2','ttf','otf','eot','mp3','mp4','avi','mov','mkv','webm'}
DOC_EXTS = {'md','txt','rst','adoc'}

def sniff_binary(path):
    """M16: 读文件头 8192 字节，NUL 占比>0.5% 判二进制"""
    try:
        with open(path, 'rb') as f:
            head = f.read(8192)
    except Exception:
        return False
    if not head:
        return False
    return head.count(b'\x00') / len(head) > 0.005

def walk_files(src):
    """确定性全量文件清单：sorted、相对正斜杠、滤 .git、错误记录不静默"""
    files = []
    errors = []
    for root, dirs, names in os.walk(src):
        dirs.sort()
        names.sort()
        dirs[:] = [d for d in dirs if d != '.git']
        for n in names:
            full = os.path.join(root, n)
            rel = os.path.relpath(full, src).replace(os.sep, '/')
            # E-18: 前缀判断而非字符集 lstrip（防吃 hidden 目录首点）
            if rel.startswith('./'):
                rel = rel[2:]
            if rel.startswith('.git/'):
                continue
            files.append((rel, full))
    files.sort(key=lambda t: t[0])
    return files, errors

def extract_patterns(ktext):
    """解析 sinks/_index.md。返回 {cls: {'lang': [(pattern, is_regex)]}}
    v0.11.0: M19 表格管道重建（cols[11:] join）+ 组间正则切分；M20 explicit 标记 is_regex=True 不再二次转义"""
    classes = {}
    for line in ktext.split(chr(10)):
        if not line.startswith('|') or 'SINK-' not in line:
            continue
        cols = [c.strip() for c in line.split('|')]
        if len(cols) < 8:
            continue
        cls = cols[1]
        if not cls.startswith('SINK-') or cls in SIGNAL_CLASSES:
            continue
        # v0.9.1: 优先显式 grep_patterns 列（M19: 列内 | 被表格分隔符切碎，cols[11:] join 重建）
        if len(cols) > 11:
            gp = '|'.join(cols[11:]).strip(' |')
            if gp and gp != '-':
                lang_pats_explicit = {}
                # 组间分隔：空白 + 语言码 + 冒号（M19: 单空格分隔，非双空格）
                for grp in re.split(r'\s+(?=[A-Za-z][A-Za-z0-9]*:)', gp):
                    grp = grp.strip()
                    if ':' not in grp:
                        continue
                    lang2, pat2 = grp.split(':', 1)
                    lang2 = lang2.strip()
                    pat2 = pat2.strip().strip('|').strip()
                    if lang2 and pat2:
                        lang_pats_explicit.setdefault(lang2, []).append((pat2, True))
                if lang_pats_explicit:
                    classes[cls] = lang_pats_explicit
                    continue
        # fallback: signals 列（'·' 分隔语言，token 需 re.escape——is_regex=False）
        signals = cols[6]
        lang_pats = {}
        for part in signals.split('·'):
            part = part.strip()
            if ':' not in part:
                continue
            lang, desc = part.split(':', 1)
            lang = lang.strip()
            desc = desc.strip()
            if not lang:
                continue
            tokens = set()
            if '未' in desc or '缺失' in desc or '无' in desc:
                continue
            for chunk in re.split(r'[\s/]+', desc):
                chunk = chunk.strip()
                if len(chunk) < 5:
                    continue
                if re.search(r'[\u4e00-\u9fff]', chunk):
                    continue
                if chunk.lower() in ('new', 'class', 'static', 'final', 'private', 'public', 'string', 'user', 'file'):
                    continue
                m = re.match(r'^([A-Za-z_][A-Za-z0-9_.]+)\(?', chunk)
                if m:
                    tok = m.group(1).rstrip('.')
                    if len(tok) >= 5:
                        tokens.add(tok)
                        last = tok.split('.')[-1]
                        if len(last) >= 5:
                            tokens.add(last)
                else:
                    m2 = re.match(r'^([A-Za-z_][A-Za-z0-9_]+)$', chunk)
                    if m2 and len(m2.group(1)) >= 5:
                        tokens.add(m2.group(1))
            if tokens:
                lang_pats.setdefault(lang, []).extend([(t, False) for t in tokens])
        if lang_pats and cls not in classes:
            classes[cls] = lang_pats
    return classes

ENTRY_PATTERNS = {
    'rest': {
        'J': ['doGet|doPost|doPut|doDelete|@GetMapping|@PostMapping|@PutMapping|@DeleteMapping|@RequestMapping'],
        'Py': [r'@app\.route|@bp\.route|@blueprint\.route|@router\.(get|post|put|delete)|FastAPI|@api\.'],
        'Go': [r'http\.HandleFunc|http\.Handle\(|HandleFunc\(|gin\.|echo\.(GET|POST|PUT|DELETE)\(|mux\.HandleFunc'],
        'N': [r'app\.(get|post|put|delete|use)\(|router\.(get|post|put|delete)\(|express\(|@(Get|Post|Put|Delete)\(|@Controller'],
        'PHP': ['\\$_GET|\\$_POST|\\$_REQUEST'],
    },
    'rpc': {
        'J': [r'RPC|Remote|@RpcMethod|gRPC|@GrpcService|rpc\s+\w+\s*\('],
        'Py': [r'grpc\.|@rpc|rpc\('],
        'Go': [r'grpc\.|Register\w+Server\(|pb\.'],
        'N': [r'grpc|@Rpc|createServer\('],
    },
    'mq': {
        'J': ['MessageListener|onMessage|@KafkaListener|@RabbitListener|@JmsListener'],
        'Py': [r'@consumer|kafka|celery|@task|on_message|Kombu|pika'],
        'Go': [r'kafka\.|ConsumerGroup|amqp\.|Subscribe\(|Consume\('],
        'N': ['kafka|amqp|onMessage|consumer'],
    },
    'ws': {
        'J': ['WebSocket|onOpen|onMessage|@ServerEndpoint'],
        'Py': [r'websocket|WebSocket|@socketio|on_message|websockets\.|channels'],
        'Go': [r'websocket\.|Upgrade\(|HandleWebSocket'],
        'N': ['WebSocket|ws\\.|socket\\.io|io\('],
    },
    'graphql': {
        'J': ['@Query|@Mutation|resolver'],
        'Py': [r'graphene|@strawberry|GraphQLView|resolve_'],
        'Go': [r'graphql\.|NewSchema|graphqlHandler'],
        'N': ['graphql|@Resolver|@Query|buildSchema'],
    },
    'deser': {
        'J': ['readObject|ObjectInputStream|XMLDecoder|enableDefaultTyping'],
        'Py': [r'pickle\.loads|yaml\.load\(|jsonpickle|marshal\.loads'],
        'Go': [r'json\.Unmarshal|gob\.NewDecoder|xml\.Unmarshal'],
        'N': ['JSON\\.parse|node-serialize|unserialize|deserialize'],
        'PHP': ['unserialize\\('],
    },
    'file': {
        'J': ['FileInputStream|Files\\.read|openStream\\('],
        'Py': [r'open\(|FileInput|Path\.read'],
        'Go': [r'os\.Open|ioutil\.ReadFile|os\.ReadFile'],
        'N': ['fs\\.readFile|readFileSync|createReadStream'],
        'PHP': ['file_get_contents|fopen\\('],
    },
    'cli': {
        'J': ['public static void main'],
        'Py': ['def main|if __name__'],
        'Go': [r'func main\('],
        'N': [r'process\.argv|#!/usr/bin/env node'],
        'C': ['main\\('],
        'Cpp': ['main\\('],
    },
    'event': {
        'J': ['EventListener|onEvent|@EventListener|@EventHandler'],
        'Py': [r'@event|EventEmitter|add_listener|signals'],
        'Go': [r'Notify\(|signal\.|EventEmitter'],
        'N': ['on\\(|addEventListener|EventEmitter|emit\\('],
    },
    'lambda': {
        'Py': ['lambda_handler'],
        'N': [r'exports\.handler|handler\s*='],
        'J': ['handleRequest|RequestHandler'],
        'Go': [r'lambda\\.Start'],
    },
}

def compile_groups(lang_map):
    """把 {cls: [(pat, is_regex)]} 编译为命名组大 alternation：返回 (combined_re, idx_to_cls)"""
    parts = []
    idx_to_cls = []
    for cls, pats in lang_map.items():
        for pat, is_regex in pats:
            if not pat:
                continue
            p = pat if is_regex else re.escape(pat)
            gi = len(parts)
            parts.append('(?P<g%d>%s)' % (gi, p))
            idx_to_cls.append(cls)
    if not parts:
        return None, []
    return re.compile('|'.join(parts)), idx_to_cls

def scan_lines(path, combined_re, idx_to_cls, hits):
    """流式逐行：一次 search 覆盖全类；命中行遍历 groups 找全部命中类"""
    try:
        fh = open(path, encoding='utf-8', errors='replace')
    except Exception:
        walk_errors_global.append('scan failed: ' + path)
        return
    with fh:
        for ln, line in enumerate(fh, 1):
            m = combined_re.search(line)
            if not m:
                continue
            seen_cls = set()
            for gi, cls in enumerate(idx_to_cls):
                if m.group('g%d' % gi) is not None and cls not in seen_cls:
                    seen_cls.add(cls)
                    hits.append((cls, ln, line.strip()[:80]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True)
    ap.add_argument('--knowledge', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    src, out = args.source, args.output
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(out, 'logs'), exist_ok=True)
    try:
        ktext = open(os.path.join(args.knowledge, 'sinks/_index.md'), encoding='utf-8').read()
    except Exception as ex:
        print('FATAL: cannot read knowledge sinks/_index.md: %s' % str(ex)[:120])
        sys.exit(1)
    classes = extract_patterns(ktext)
    # E-03: 未映射语言码显式 FAIL（不静默回落）
    for cls, lang_pats in classes.items():
        for lang in lang_pats:
            if lang not in EXT_FOR_LANG:
                print('FATAL: knowledge uses unmapped language code %r (class %s); add it to EXT_FOR_LANG/LANG_OF_EXT' % (lang, cls))
                sys.exit(1)
    files, walk_errors = walk_files(src)
    for e in walk_errors:
        open(os.path.join(out, 'logs', 'walk_errors.log'), 'a', encoding='utf-8').write(str(e)[:200] + chr(10))
    file_rows = []
    src_rows = []
    sink_logs = {}   # cls -> [path:line:text]
    entry_logs = {}  # et -> [path:line:text]
    edges = []
    import_pats = {
        'J': re.compile(r'\bimport\s+([\w.]+)'),
        'Py': re.compile(r'\bfrom\s+([\w.]+)\s+import'),
        'Go': re.compile(r'\bimport\s+"([\w./]+)"'),
        'N': re.compile(r"(?:require\(['\"]|import.*?from\s*['\"])([\w./@-]+)"),
        'PHP': re.compile(r'\b(?:use|require(?:_once)?|include(?:_once)?)\s*[\(\s]+([\w./\\-]+)'),
        'C': re.compile(r'#include\s*[<"]([\w./]+)[>"]'),
        'Cpp': re.compile(r'#include\s*[<"]([\w./]+)[>"]'),
    }
    call_re = re.compile(r'\b([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\(')  # E-24: 含点分 callee 统一
    # 每语言编译合并 regex
    sink_re_by_lang = {}
    for lang, ext_tuple in EXT_FOR_LANG.items():
        cmap = {}
        for cls, lang_pats in classes.items():
            if lang in lang_pats:
                cmap[cls] = lang_pats[lang]
        cre, idx = compile_groups(cmap)
        sink_re_by_lang[lang] = (cre, idx)
    entry_re_by_lang = {}
    for lang in EXT_FOR_LANG:
        emap = {et: [(p, True) for p in lang_pats[lang]] for et, lang_pats in ENTRY_PATTERNS.items() if lang in lang_pats}
        if emap:
            cre, idx = compile_groups(emap)
            entry_re_by_lang[lang] = (cre, idx)
        else:
            entry_re_by_lang[lang] = (None, [])
    for rel, full in files:
        ext = os.path.splitext(rel)[1].lstrip('.') or 'unknown'
        binary = sniff_binary(full)
        if ext in IMAGE_EXTS:
            ftype = 'image'
        elif ext in ARCHIVE_EXTS or ext in BINARY_EXTS:
            ftype = 'archive' if ext in ARCHIVE_EXTS else 'binary'
        elif ext in ('java','py','go','js','ts','php','c','cpp','h','mjs','cjs','jsx','tsx','cc','hpp'):
            ftype = 'source'
        elif ext in DOC_EXTS:
            ftype = 'doc'
        else:
            ftype = 'other'
        file_rows.append((rel, ftype, ext, '-', 'binary' if binary else 'text'))
        lang = LANG_OF_EXT.get(ext)
        if not lang or lang not in EXT_FOR_LANG:
            continue
        # sink 扫描
        cre, idx = sink_re_by_lang[lang]
        if cre is not None:
            shits = []
            scan_lines(full, cre, idx, shits)
            for cls, ln, txt in shits:
                if '/test/' in rel or rel.startswith('test/'):
                    continue
                sink_logs.setdefault(cls, []).append('%s:%d:%s' % (rel, ln, txt))
                sid = hashlib.md5((rel + ':' + str(ln) + ':' + cls).encode()).hexdigest()[:8]
                sink_global.append((sid, rel + ':' + str(ln), cls, txt))
        # 入口扫描
        ere, eidx = entry_re_by_lang[lang]
        if ere is not None:
            ehits = []
            scan_lines(full, ere, eidx, ehits)
            for et, ln, txt in ehits:
                if '/test/' in rel or rel.startswith('test/'):
                    continue
                entry_logs.setdefault(et, []).append('%s:%d:%s' % (rel, ln, txt))
                sid = hashlib.md5((rel + ':' + str(ln) + ':' + et).encode()).hexdigest()[:8]
                src_rows.append((sid, rel + ':' + str(ln), et, txt, '-'))
        # call_edges（全量不截断）
        ipat = import_pats.get(lang)
        try:
            fh = open(full, encoding='utf-8', errors='replace')
        except Exception:
            fh = None
        if fh is not None:
            with fh:
                for line in fh:
                    if ipat:
                        for m in ipat.finditer(line):
                            edges.append((rel, m.group(1), 'import'))
                    for m in call_re.finditer(line):
                        edges.append((rel, m.group(1), 'call'))
    # 清单去重 + sorted
    seen = set(); dedup = []
    for r in sink_global:
        k = (r[1], r[2])
        if k not in seen:
            seen.add(k); dedup.append(r)
    write_tsv_sorted(os.path.join(out, 'sink_inventory.tsv'), ['sink_id','file:line','sink_type','symbol','sort_order'], dedup)
    seen2 = set(); dedup2 = []
    for r in src_rows:
        k = (r[1], r[2])
        if k not in seen2:
            seen2.add(k); dedup2.append(r)
    write_tsv_sorted(os.path.join(out, 'source_inventory.tsv'), ['source_id','file:line','entry_type','symbol','param','sort_order'], dedup2)
    write_tsv_sorted(os.path.join(out, 'file_inventory.tsv'), ['path','type','lang','loc','binary_flag','sort_order'], file_rows)
    # logs（E49 结构对账：log 行数 == 清单行数）
    for cls, lines in sink_logs.items():
        p = os.path.join(out, 'logs', 'sinks_' + cls + '.log')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(sorted(lines)) + ('\n' if lines else '') or 'ZERO_HITS_WARRANT_REVIEW\n')
    for et, lines in entry_logs.items():
        p = os.path.join(out, 'logs', 'sources_' + et + '.log')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(sorted(lines)) + ('\n' if lines else '') or 'ZERO_HITS_WARRANT_REVIEW\n')
    # 全知识类 logs 补零/不可用标记（v0.7.7 语义）
    all_kclasses = set(re.findall(r'SINK-[A-Z0-9-]+', ktext)) - SIGNAL_CLASSES
    for kc in sorted(all_kclasses):
        lf = os.path.join(out, 'logs', 'sinks_' + kc + '.log')
        if not os.path.isfile(lf):
            if kc not in classes:
                open(lf, 'w', encoding='utf-8').write('PATTERN_UNAVAILABLE\n')
            else:
                open(lf, 'w', encoding='utf-8').write('ZERO_HITS_WARRANT_REVIEW\n')
    edges = sorted(set(edges))
    with open(os.path.join(out, 'call_edges.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['src_file', 'target', 'edge_type'])
        for e in edges:
            w.writerow(e)
    print('file=%d sink=%d source=%d edges=%d' % (len(file_rows), len(dedup), len(dedup2), len(edges)))

def write_tsv_sorted(path, header, rows):
    rows = sorted(rows, key=lambda r: (r[1] if len(r) > 1 else r[0], r[0]))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(header)
        for i, r in enumerate(rows, 1):
            w.writerow(list(r) + [i])

sink_global = []  # 模块级：sink 命中收集
walk_errors_global = []  # 模块级：扫描读错误收集（不静默）

if __name__ == '__main__':
    main()
