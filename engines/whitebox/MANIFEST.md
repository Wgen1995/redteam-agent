# whitebox 车道A 解析器 MANIFEST（契约 08 十二字段）

kind: cli

| 字段 | 值 |
|---|---|
| name | whitebox-lane-a |
| kind | cli（纯本地确定性解析: 源码目录+GenSift .pattern 流入→谱图工件流出,无网络、无 OS 工具依赖） |
| version | 0.1.0（W4 第一段: parser_v0+锚边契约） |
| 适用场景 | 白盒车道A: 源码→codegraph.jsonl（符号表+调用边）+pattern-hits.jsonl+digest 事实——L2 只入工件（密度律） |
| 参数 | parser_v0.py --source-dir=S --out-dir=D [--patterns-dir=P（缺省 knowledge/staging/gensift-intake/classes/patterns）] |
| 产物路径 | {out-dir}/codegraph.jsonl + pattern-hits.jsonl + digest.json（仅此三件;引擎不写账本） |
| 超时 | 秒级（千文件级库线性扫描;ast-grep 级加速留后续舰） |
| 重试策略 | 不适用（确定性变换: 同输入逐字节同输出,金样可重放钉死） |
| 幂等键 | {source-dir 内容}+{patterns-dir 内容}（digest.codegraph_sha256 随内容变） |
| 纪律能力声明 | max_op_level: 读／视角上限: L0（纯解析,零执行目标代码） |
| 工具依赖 | Python3 标准库（ast/re/json/hashlib）——GenSift 方言(b)翻译内建,无 grep 依赖 |
| 验签公钥 | 不适用 |

## 密度律执法（source-audit-v1 §1.2）

文件入口入账（L0/L1,总控验收 digest 后落）/符号调用入工件（L2,codegraph.jsonl）/
污点入卡（L3,intents）/结论回账。本引擎只产工件+digest 事实一条
（kind=codegraph-digest: 符号数/边数/sha256/解析器版本）——**不写账本**;
锚边 anchor（第 11 边型,contracts/01-ledger-schema.md v2 勘误）provenance 的
file:line+工件 sha256 即由 pattern-hits.jsonl 与 digest 提供。

## GenSift .pattern 翻译（#15-3 裁决: 方言(b)）

- POSIX 括号类按表展开八类（space/alnum/upper/lower/digit/alpha/xdigit/blank）,
  含混合括号形态（如 CI-P12 的 `(^|[[:space:](=,])eval\`）;
- 表外 POSIX 类（graph/print/cntrl/punct…）与 Python re 编译不过的语法
  （含 GNU \< \> 词边界——Python 静默读成字面尖括号）一律**跳过并记录**
  （digest.patterns.skipped,逐条带 class/lang/pattern_id/ere/reason）——诚实,不猜;
- ERE 单字符括号类 `[[]` 机械归一为 `\\[`（等价,消 FutureWarning）;
- 语义等价基准: fixtures/enum pos 命中集=manifest expected_patterns（GenSift
  grep -E 实跑口径）,neg 零命中——tests/test_whitebox_parser_v0.py 钉死。

## 签名哈希口径

- symbol.sig_sha256 = sha256(signature 文本)——signature=name(参数列表)
  （python 含 self/默认形参名;java/ts 原文参数串空白归一）;
- call.sig_sha256 = sha256("callee(argc)")——调用点用法签名（argc=顶层参数计数,
  行级近似口径）;行号不进哈希（防位置平移换 ID,同设计 L3 dedup 律精神）。

## v0 能力边界（如实披露,不夸大）

- Java/TS 符号与调用=行级正则启发（无完整语法树）: 构造器不建符号、
  链式调用同行多 callee 逐个落、跨行调用不追;python=ast 全量;
- callee_symbol 仅同名唯一时回填,否则 null（诚实不猜）;
- 命中行原文不入工件（secrets 类防密值外流;复核走 file:line 指针）;
- digest 含 unparsed_files（python 语法错误文件计数,如实入账）。
