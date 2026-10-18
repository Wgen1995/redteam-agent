# -*- coding: utf-8 -*-
"""兵种运行时（F4 收尾件）——五兵种卡从数据变成可指派的配置对象。

锚点：
- 对照账 docs/design/2026-10-20-capability-comparison-ledger.md F4:50——兵种
  =六维配置包，「加兵种=加模板零运行时代码」；总控派单走 steer 通道+意图行
  带兵种位。F9:90 兵种 YAML=配置对象单源。五兵种卡已落（297e2b0：recon/
  enum/exploit/verify/commander，六维 frontmatter+24 结构测试钉面）——本
  件把卡面读成运行时对象：加载/路由/越权执法三面，纯函数零侧效。
- 裁决书 §六军团编制六维=permissions/tools/llm_route/backend/trigger/
  artifacts（卡面 frontmatter 即缺省值）。
- 兵种位承载=意图 detail 虚拟列方括号标记（[prereq:]/[owner:]/[lease:]
  先例同形）：[corps:pentest-recon]——commander 卡纪律 2「派单带兵种位」。

Ruling：
- R-CORPS-1 路由缺省为何这四映射：与 commander 卡纪律 2 逐字一致
  （recon→侦察兵/surface→枚举兵/matrix-test+deep-dive→渗透兵/nday-verify→
  验证官），且逐一对应五卡 trigger 维的 kind 面。authz-diff 无缺省路由：
  F6 业务逻辑层在飞无卡可承，缺省塞给渗透兵=差分意图静默走 web 工具面
  （错兵种错卡），fail-loud 强迫 corps.yaml routes 显式指定。commander
  不入 kind 路由：常驻调度位（战役建立即位），按意图派会把调度兵当
  作戦兵开枪——只经兵种位直读指派。
- R-CORPS-2 越权拒的执法点选型：spawn 时执行器前置纯函数（loop 的
  _guarded_tool_exec 判定前置同形，guardrail.Admission 同构面），而非
  执行后审计/卡文自律/registry 层拦截。理由：权限集是兵种属性
  （per-corps 面），registry 是全局命令面无兵种上下文拦不了；执行前拒
  =越权命令零成本（没跑就没副作用）；纯函数=可单测可复放。与 guardrail
  串联不替代——分层执法：兵种面（谁有权）→范围面（目标界内否）→风险面
  （动作危险否），本件只占第一层。
- R-CORPS-3 配置只收不放：corps.yaml 可裁兵种/改默认路由/收窄卡面，
  扩面（卡面外命令/工具）一律拒——放权只经卡面（SKILL.md 过 297e2b0
  结构测试），yaml 是部署收窄面不是扩权面。
- R-CORPS-4 零 yaml 依赖：仓内先例（tests 手解析 frontmatter），
  corps.yaml 走文档化子集微解析，PyYAML 不进依赖树。

装配位（loop.py 修复舰落舱后由总控接一行，本件零改 loop/执行器）：
    # __init__ 装配段：
    self.corps_rt = corps_mod.load_corps(goal_dir)
    # 领单后（简报=兵种卡面，ContextBuilder 的 skill_path 注入位）：
    corps = self.corps_rt.resolve(intent)
    # 工具/账本指令执行前置（与判定门串联，拒=rc1+reason 回模型面）：
    adm = corps_mod.authorize(corps, cmd)
    if not adm.allowed: return 1, "", adm.reason

跑法：python3 -m unittest tests.test_corps -v
"""
import importlib
import os
import re

__all__ = ["CorpsError", "Corps", "Authorization", "CorpsRuntime",
           "load_corps", "authorize", "marker_of", "SKILL_CORPS",
           "DEFAULT_KIND_ROUTES"]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SKILLS_DIR = os.path.join(REPO_ROOT, ".opencode", "skills")

# 五兵种（297e2b0 卡序=侦察/枚举/渗透/验证官/总控；report=旧卡 168fc00，
# frontmatter 四维非六维，后续卡位）。
SKILL_CORPS = ("pentest-recon", "pentest-enum", "pentest-exploit",
               "pentest-verify", "pentest-commander")

# contracts/01 六 kind（intents.tsv kind 枚举单源）。
SIX_KINDS = ("recon", "surface", "matrix-test", "deep-dive", "authz-diff",
             "nday-verify")

# 缺省 kind 路由（commander 卡纪律 2 逐字；authz-diff 故意缺席=R-CORPS-1）。
DEFAULT_KIND_ROUTES = {
    "recon": "pentest-recon",
    "surface": "pentest-enum",
    "matrix-test": "pentest-exploit",
    "deep-dive": "pentest-exploit",
    "nday-verify": "pentest-verify",
}

# 兵种位标记（detail 虚拟列方括号先例同形：[corps:<name>]）。
_CORPS_RE = re.compile(r"\[corps:([^\[\]\s]+)\]")

# handler 内写形三条（registry.py 顶部注释口径：写路径锁在 handler 内部，
# registry 层不拆读写形）——并入写面白名单派生源。
_IN_HANDLER_WRITES = frozenset(("retest-scan", "retest-settle",
                                "set-replay-state"))

# corps.yaml 合法顶级键（拼错键=fail-loud，防配置静默失效）。
_CONFIG_KEYS = ("disabled", "routes", "corps")
_CORPS_OVERRIDE_KEYS = ("ledger", "cards", "llm_route", "backend")

_WRITE_FACE = None            # 写命令面缓存（registry 单源派生）


class CorpsError(Exception):
    """兵种运行时 fail-loud 面：路由无解/配置矛盾/面外扩权。"""


def marker_of(detail):
    """detail → 兵种位名（无标记=空串；[prereq:]/[owner:] 标记不误触）。"""
    m = _CORPS_RE.search(str(detail or ""))
    return m.group(1) if m else ""


def _writer_face():
    """写命令面（单源派生禁手抄）：registry 写命令注册表各模块 HANDLERS
    键集 ∪ handler 内写形三条。私有属性只读引用（registry 模块 docstring
    即此口径），不改运行时。"""
    global _WRITE_FACE
    if _WRITE_FACE is None:
        face = set(_IN_HANDLER_WRITES)
        from ledger import registry
        for m in registry._WRITER_MODULES:
            try:
                mod = importlib.import_module("ledger." + m)
            except ImportError:
                continue
            face |= set(getattr(mod, "HANDLERS", {}))
        _WRITE_FACE = frozenset(face)
    return _WRITE_FACE


# ---- 卡面解析（frontmatter 微解析——仓内零 yaml 依赖先例）--------------------

def _flow_items(v):
    return [t.strip() for t in v[1:-1].split(",") if t.strip()]


def _parse_front(text):
    """SKILL.md frontmatter → dict。形制：顶层 key: 单行值；tools: 嵌套
    两键 ledger:/cards: 流列表（与 tests/test_soldier_cards.py 同形制）。"""
    fm, key = {}, None
    for ln in text.split("---", 2)[1].splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if ln.startswith("  ") and key:
            body = ln.strip()
            if ":" not in body:
                continue
            k, v = body.split(":", 1)
            v = v.strip()
            fm.setdefault(key, {})[k.strip()] = (_flow_items(v)
                                                 if v.startswith("[")
                                                 and v.endswith("]") else v)
        elif ":" in ln and not ln.startswith(" "):
            key = ln.split(":", 1)[0].strip()
            v = ln.split(":", 1)[1].strip()
            if v.startswith("[") and v.endswith("]"):
                fm[key] = _flow_items(v)
                key = None
            elif v == "":
                fm[key] = {}
            else:
                fm[key] = v
                key = None
    return fm


def _load_card(name):
    """兵种卡 → Corps 配置对象（六维缺省面+写面白名单派生）。"""
    path = os.path.join(SKILLS_DIR, name, "SKILL.md")
    with open(path, encoding="utf-8") as f:
        fm = _parse_front(f.read())
    tools = fm.get("tools") or {}
    ledger = frozenset(str(x) for x in (tools.get("ledger") or []))
    cards = frozenset(str(x) for x in (tools.get("cards") or []))
    writes = ledger & _writer_face()
    return Corps(name, ledger, cards, writes,
                 str(fm.get("llm_route") or ""), str(fm.get("backend") or ""),
                 path)


# ---- 配置面解析（corps.yaml 微解析——文档化子集，R-CORPS-4）------------------

def _parse_config(text):
    """corps.yaml → dict。子集：顶级键 disabled/routes/corps；块列表
    （- x）/流列表（[a, b]）/空映射（{}）/标量；corps 下两段缩进
    （兵种名→覆盖键: 值）。# 注释与空行忽略；他形 fail-loud。"""
    cfg, section, sub = {}, None, None
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        stripped = stripped.split(" #")[0].strip()
        if not stripped:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent == 0:
            top, _, v = stripped.partition(":")
            top, v = top.strip(), v.strip()
            if top not in _CONFIG_KEYS:
                raise CorpsError("corps.yaml 未知顶级键: %r（可用: %s）"
                                 % (top, "/".join(_CONFIG_KEYS)))
            section, sub = top, None
            if v.startswith("[") and v.endswith("]"):
                cfg[top] = _flow_items(v)
                section = None
            elif v == "{}":
                cfg[top] = {}
                section = None
            elif v:
                cfg[top] = v
                section = None
            else:
                cfg[top] = [] if top == "disabled" else {}
        elif indent == 2 and section:
            if stripped.startswith("- "):
                if not isinstance(cfg[section], list):
                    raise CorpsError("corps.yaml %s 是映射不可列项: %r"
                                     % (section, stripped))
                cfg[section].append(stripped[2:].strip())
                continue
            k, _, v = stripped.partition(":")
            k, v = k.strip(), v.strip()
            if section == "routes":
                if not v:
                    raise CorpsError("corps.yaml routes 空值: %r" % stripped)
                cfg["routes"][k] = v
            elif section == "corps":
                if v:
                    raise CorpsError("corps.yaml 兵种覆盖须块形（%s: 下缩进）"
                                     % section)
                sub = k
                cfg["corps"][k] = {}
            else:
                raise CorpsError("corps.yaml disabled 不可映射: %r" % stripped)
        elif indent >= 4 and section == "corps" and sub:
            k, _, v = stripped.partition(":")
            k, v = k.strip(), v.strip()
            if k not in _CORPS_OVERRIDE_KEYS:
                raise CorpsError("corps.yaml 未知覆盖键: %r（可用: %s）"
                                 % (k, "/".join(_CORPS_OVERRIDE_KEYS)))
            cfg["corps"][sub][k] = (_flow_items(v) if v.startswith("[")
                                    and v.endswith("]") else v)
        else:
            raise CorpsError("corps.yaml 形不识别: %r" % raw)
    return cfg


# ---- 运行时对象 ---------------------------------------------------------------

class Corps(object):
    """兵种配置对象（六维卡面的运行时形；frozenset 面=只读律）。"""

    __slots__ = ("name", "ledger", "cards", "write_allow", "llm_route",
                 "backend", "skill_path")

    def __init__(self, name, ledger, cards, write_allow, llm_route,
                 backend, skill_path):
        self.name = name
        self.ledger = frozenset(ledger)
        self.cards = frozenset(cards)
        self.write_allow = frozenset(write_allow)
        self.llm_route = llm_route
        self.backend = backend
        self.skill_path = skill_path

    def __repr__(self):
        return "Corps(%s ledger=%d cards=%d writes=%d)" % (
            self.name, len(self.ledger), len(self.cards),
            len(self.write_allow))


class Authorization(object):
    """authorize 的裁决面（guardrail.Admission 同构：allowed/stage/reason）。

    stage ∈ ledger/card（面内放行）/ write（写面越权拒）/ face（面外命令拒）/
    route（路由无解拒）/ fail-closed（校验异常拒）。
    """

    __slots__ = ("allowed", "stage", "reason")

    def __init__(self, allowed, stage, reason):
        self.allowed = bool(allowed)
        self.stage = stage
        self.reason = str(reason or "")


def authorize(corps, command):
    """越权执法点（执行器前置校验形，纯函数，永不 raise）。

    序：账本命令面 → 工具卡面 → 写面越权拒 → 面外拒。面内=放行；
    写命令不在白名单=write 拒；其余=face 拒。内部异常折叠 fail-closed 拒
    （坏门=关门，guardrail 同律）。
    """
    try:
        cmd = str(command if command is not None else "").strip()
    except Exception as e:                              # noqa: BLE001
        return Authorization(False, "fail-closed", "命令形异常，拒: %s" % e)
    if corps is None or not cmd:
        return Authorization(False, "face", "无兵种上下文或空命令，拒")
    try:
        if cmd in corps.ledger:
            return Authorization(True, "ledger",
                                 "%s 账本命令面内" % corps.name)
        if cmd in corps.cards:
            return Authorization(True, "card", "%s 工具卡面内" % corps.name)
        if cmd in _writer_face():
            return Authorization(
                False, "write",
                "写面越权: %s 不在 %s 写面白名单（兵种权限集外命令直接拒，"
                "卡面纪律见 %s）" % (cmd, corps.name, corps.skill_path))
    except Exception as e:                              # noqa: BLE001
        return Authorization(False, "fail-closed",
                             "兵种面校验异常，按 fail-closed 拒: %s" % e)
    return Authorization(
        False, "face", "面外命令: %s 不在 %s 命令面" % (cmd, corps.name))


class CorpsRuntime(object):
    """一场仗的兵种编制：卡面缺省 + corps.yaml 收窄 + 路由/执法面。"""

    def __init__(self, config=None):
        cfg = config or {}
        unknown = {str(d) for d in cfg.get("disabled", ())} - set(SKILL_CORPS)
        if unknown:
            raise CorpsError("corps.yaml 裁未知兵种: %s（五兵种: %s）"
                             % (sorted(unknown), "/".join(SKILL_CORPS)))
        self._disabled = frozenset(cfg.get("disabled", ()))
        self._enabled = [n for n in SKILL_CORPS if n not in self._disabled]
        self._base = {n: _load_card(n) for n in SKILL_CORPS}

        routes = dict(DEFAULT_KIND_ROUTES)
        for kind, target in (cfg.get("routes") or {}).items():
            if kind not in SIX_KINDS:
                raise CorpsError("corps.yaml 路由键非 contracts/01 六 kind: %r"
                                 % kind)
            if target not in self._base:
                raise CorpsError("corps.yaml 路由指向未知兵种: %r" % target)
            if target in self._disabled:
                raise CorpsError("corps.yaml 路由指向已裁兵种: %s→%s"
                                 % (kind, target))
            routes[kind] = target
        # 缺省路由随裁剪枝（显式改道上文已校验不指裁兵；缺省被裁=派单时
        # fail-loud 附原缺省名，R-CORPS-1 不静默改道）。
        self._routes = {k: t for k, t in routes.items()
                        if t not in self._disabled}

        self._final = dict(self._base)
        for name, ov in (cfg.get("corps") or {}).items():
            if name not in self._base or name in self._disabled:
                raise CorpsError("corps.yaml 覆盖未知/已裁兵种: %r" % name)
            base = self._base[name]
            ledger, cards = base.ledger, base.cards
            if "ledger" in ov:
                want = frozenset(str(x) for x in ov["ledger"])
                widen = want - base.ledger
                if widen:
                    raise CorpsError("corps.yaml 扩权（卡面外账本命令）: %s"
                                     % sorted(widen))
                ledger = want
            if "cards" in ov:
                want = frozenset(str(x) for x in ov["cards"])
                widen = want - base.cards
                if widen:
                    raise CorpsError("corps.yaml 扩权（卡面外工具卡）: %s"
                                     % sorted(widen))
                cards = want
            self._final[name] = Corps(
                name, ledger, cards, ledger & _writer_face(),
                str(ov.get("llm_route") or base.llm_route),
                str(ov.get("backend") or base.backend), base.skill_path)

    # ---- 查询面 ----

    def enabled(self):
        """在编兵种名列表（卡序稳定）。"""
        return list(self._enabled)

    def corps(self, name):
        """兵种名 → 配置对象（未知/已裁=fail-loud）。"""
        if name not in self._base:
            raise CorpsError("未知兵种: %r（五兵种: %s）"
                             % (name, "/".join(SKILL_CORPS)))
        if name in self._disabled:
            raise CorpsError("兵种已被 corps.yaml 裁掉: %s" % name)
        return self._final[name]

    def routes(self):
        """生效 kind 路由快照（缺省∪改道，裁兵种行已剪）。"""
        return dict(self._routes)

    # ---- 路由面 ----

    def resolve(self, intent_row):
        """意图行 → 兵种对象。兵种位（[corps:X]）直读优先；缺省按 kind
        路由（R-CORPS-1）。无解=fail-loud，绝不静默兜底。"""
        row = intent_row or {}
        mark = marker_of(row.get("detail"))
        if mark:
            return self.corps(mark)
        kind = str(row.get("kind") or "").strip()
        if not kind:
            raise CorpsError("意图行缺 kind 且无兵种位，无法路由: %r"
                             % row.get("id"))
        target = self._routes.get(kind)
        if target is None:
            was = DEFAULT_KIND_ROUTES.get(kind)
            if was:
                raise CorpsError("kind=%s 缺省兵种 %s 已被 corps.yaml 裁掉"
                                 "（改道须 routes: 显式指定）" % (kind, was))
            if kind == "authz-diff":
                raise CorpsError("kind=authz-diff 无缺省兵种（F6 业务逻辑层"
                                 "在飞无卡可承；须 corps.yaml routes 显式"
                                 "指定）")
            raise CorpsError("kind=%s 不在 contracts/01 六 kind 路由面"
                             % kind)
        return self._final[target]

    def authorize(self, command, intent_row):
        """便捷执法面：先路由后校验（路由无解=route 拒不 raise）。"""
        try:
            c = self.resolve(intent_row)
        except CorpsError as e:
            return Authorization(False, "route", "兵种路由失败，拒: %s" % e)
        return authorize(c, command)


def load_corps(goal_dir=None, corps_path=None):
    """加载兵种编制。缺省零配置=五兵种全开（卡面为缺省）；显式 corps_path
    （--corps 旗标位）优先于 <goal_dir>/corps.yaml。文件在而不可读/形错
    =fail-loud（CorpsError）。"""
    path = corps_path
    if path is None and goal_dir is not None:
        cand = os.path.join(goal_dir, "corps.yaml")
        path = cand if os.path.isfile(cand) else None
    cfg = {}
    if path is not None:
        with open(path, encoding="utf-8") as f:
            cfg = _parse_config(f.read())
    return CorpsRuntime(cfg)
