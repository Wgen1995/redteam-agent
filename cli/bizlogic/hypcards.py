# -*- coding: utf-8 -*-
"""作弊假设卡模板(功能6·设计§3 判据先行+§5 可逆纪律)——engine-hyp 卡形。

LLM 业务流还原(浏览→下单→支付→…)产出的作弊假设(能改价吗/优惠券能重用吗/能跳过
支付吗/取消后还能发货吗)走本模板铸卡,经既有 ledger-add-intent 命令面入活池
(与白盒/渗透同池同调度,engine-fusion §2 口径)——本模块不自建调度。

纪律:
- 判据先行(GenSift 吸收,设计§3): 每条假设必带 truth_criteria(判真标准)——
  先写「怎么判真」再动手;无判据=CardReject,不立卡。
- 可逆纪律(设计§5): reversibility∈{rollback-able,test-account,irreversible};
  test-account→须挂测试账号 CRED;rollback-able→须带 rollback_cmd(核销义务);
  irreversible 且无测试账号→approval_required=True(挂审批等人放行,不自动执行)。
- 池兼容如实探测: kind=engine-hyp 是否已入 write_cmds._INTENT_KINDS 枚举由
  pool_status() 运行时单源读出——未入枚举=诚实报 pending-enum(卡可铸造可校验,
  入池等枚举勘误);绝不私扩枚举/绕过命令面(write_cmds=兄弟舰领地,本舰零写入)。
- 判重纪律(契约 01): dedup_key 由命令机械计算——卡只给 dedup_key_proposed 提议。
- detail 承载: 结构化字段以 JSON 进 intents.detail 列(零 schema 改动,
  differential.md 提交模板 dedup_key_proposed 同先例)。
"""
import json

ENGINE_HYP_KIND = "engine-hyp"
CARD_ORIGIN = "llm"
REVERSIBILITY = ("rollback-able", "test-account", "irreversible")


class CardReject(Exception):
    """卡铸造/校验拒收(判据缺失/可逆纪律缺位)——fail-closed,不产半卡。"""


def make_card(hypothesis, truth_criteria, reversibility, title, target,
              biz_step, test_account_cred="", rollback_cmd="",
              expected_signal="", preconditions=(), provenance="llm-bizflow-restore"):
    """铸卡(先校验后产出): 返回 engine-hyp 卡 dict。

    expected_signal=预期差分形(哪轴/哪状态),供差分探测器对拍——判据先行的探测面。
    """
    errs = _validate_core(hypothesis, truth_criteria, reversibility,
                          test_account_cred, rollback_cmd)
    if errs:
        raise CardReject(";".join(errs))
    approval = reversibility == "irreversible" and not test_account_cred
    return {"kind": ENGINE_HYP_KIND, "origin": CARD_ORIGIN,
            "title": title, "hypothesis": hypothesis,
            "truth_criteria": list(truth_criteria),
            "reversibility": reversibility,
            "test_account_cred": test_account_cred,
            "rollback_cmd": rollback_cmd,
            "approval_required": approval,
            "target": target, "biz_step": biz_step,
            "expected_signal": expected_signal,
            "preconditions": list(preconditions),
            "provenance": provenance}


def _validate_core(hypothesis, truth_criteria, reversibility,
                   test_account_cred, rollback_cmd):
    """核心纪律校验: 返回错误清单(空=过)。"""
    errs = []
    if not (hypothesis or "").strip():
        errs.append("hypothesis 空: 假设本身必填")
    if not truth_criteria or not [c for c in truth_criteria if str(c).strip()]:
        errs.append("truth_criteria 空: 判据先行——先写判真标准再动手(设计§3)")
    if reversibility not in REVERSIBILITY:
        errs.append("reversibility 不在枚举 {rollback-able,test-account,irreversible}: "
                    + str(reversibility))
    if reversibility == "test-account" and not test_account_cred:
        errs.append("test-account 须挂测试账号 CRED 行(可逆纪律§5)")
    if reversibility == "rollback-able" and not (rollback_cmd or "").strip():
        errs.append("rollback-able 须带 rollback_cmd 核销义务(可逆纪律§5)")
    return errs


def validate_card(card):
    """整卡校验(铸后复查/入池前把关): 返回错误清单(空=过)。"""
    if not isinstance(card, dict):
        return ["卡非 dict"]
    errs = _validate_core(card.get("hypothesis", ""),
                          card.get("truth_criteria") or [],
                          card.get("reversibility", ""),
                          card.get("test_account_cred", ""),
                          card.get("rollback_cmd", ""))
    for k in ("title", "target", "biz_step", "kind", "origin"):
        if not str(card.get(k, "")).strip():
            errs.append("%s 空: 卡必填面" % k)
    if card.get("kind") != ENGINE_HYP_KIND:
        errs.append("kind 须=engine-hyp: " + str(card.get("kind")))
    if "approval_required" not in card:
        errs.append("approval_required 缺失: 可逆纪律落字段(设计§5)")
    return errs


def needs_approval(card):
    """不可逆且无测试账号 → True(挂审批等人放行)。"""
    return bool(card.get("approval_required"))


def to_add_intent_args(card):
    """卡→既有 ledger-add-intent 命令面参数 dict(kind=engine-hyp,origin=llm)。

    detail=JSON 承载结构化判据/可逆字段(零 schema 改动);
    dedup_key_proposed=提议(命令机械判重,LLM 只提议——契约 01);
    入池前置=pool_status() 为 ok(枚举勘误后),否则总控侧如实挂起。
    """
    errs = validate_card(card)
    if errs:
        raise CardReject(";".join(errs))
    payload = {"title": card["title"],
               "hypothesis": card["hypothesis"],
               "truth_criteria": card["truth_criteria"],
               "reversibility": card["reversibility"],
               "test_account_cred": card.get("test_account_cred", ""),
               "rollback_cmd": card.get("rollback_cmd", ""),
               "approval_required": card.get("approval_required", False),
               "target": card["target"],
               "biz_step": card["biz_step"],
               "expected_signal": card.get("expected_signal", ""),
               "preconditions": card.get("preconditions", []),
               "provenance": card.get("provenance", "llm-bizflow-restore")}
    return {"title": "[engine-hyp] " + card["title"],
            "detail": json.dumps(payload, ensure_ascii=False),
            "kind": ENGINE_HYP_KIND,
            "origin": CARD_ORIGIN,
            "engine": "web-blackbox",
            "asset": card["target"],
            "budget-share": "5k;50;0.5",
            "cred": card.get("test_account_cred", ""),
            "dedup_key_proposed": "%s+engine-hyp+%s" % (card["target"], card["biz_step"])}


def pool_status(kinds=None):
    """池兼容探测(单源读): kinds 显式注入=测试面;缺省读 write_cmds._INTENT_KINDS。

    返回 (ok, detail): ok=True=kind 已入枚举可入池;False=detail 含 pending-enum
    (卡可铸造可校验,入池等 write_cmds 枚举勘误——兄弟舰领地,本舰不碰)。
    """
    if kinds is None:
        try:
            from ledger import write_cmds
            kinds = write_cmds._INTENT_KINDS
        except Exception as e:   # noqa: BLE001 —— 探测面如实报,不猜枚举
            return False, "pending-enum: write_cmds 不可读(%s)——入池通道待确认" % e
    if ENGINE_HYP_KIND in (kinds or set()):
        return True, ("ok: intents kind 枚举已含 engine-hyp——卡经 ledger-add-intent "
                      "入活池,与白盒/渗透同池同调度")
    return False, ("pending-enum: intents kind 枚举暂无 engine-hyp(engine-fusion "
                   "勘误未落)——卡可铸造/校验,入池须等枚举勘误(本舰不私扩 write_cmds)")
