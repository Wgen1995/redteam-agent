# -*- coding: utf-8 -*-
"""工具卡注册表（W3·蓝图 25 张）——工具=数据不是代码。

每张卡=纪律字段齐备的数据结构（七字段缺一不可，discipline_errors 机械校验）：
  名称 name / 档位 tier（L0-L3，L3=破坏性·横移必人审）/ 限速 rate（RoE 标注，
  带执法旗标的卡在 gate 层机械固化）/ 黑名单覆盖 deny_extra（全局 DENYLIST 之外的
  本卡增补拒绝模式）/ revert 义务 revert（有副作用卡核销义务；只读卡显式
  none(只读)——显式声明而非留空）/ 示例命令 example / 风险级 risk。

档位口径（AGENTS L0-L3 标注律）：L0 本地无流量 / L1 远程只读主动 / L2 主动高敏
或可写（带 revert 义务）/ L3 破坏性·横移·凭据攻击执行——未批即拒（审批门挂卡=
approvals.tsv command_hash 对照，见 gate.py）。
"""
import re

TIERS = ("L0", "L1", "L2", "L3")
RISKS = ("low", "medium", "high", "critical")
RATE_RE = re.compile(r"^(\d+/(s|m)|local|serial)$")
READONLY_REVERT = "none(只读)"
READONLY_PREFIX = "none(只读"


class CardError(Exception):
    """注册表纪律错误（重名/字段不备/值域外）。"""


class ToolCard:
    """工具卡数据结构——七纪律字段+分类元数据；行为只有机械校验，无执行逻辑。"""

    __slots__ = ("name", "binary", "tier", "rate", "deny_extra", "revert",
                 "example", "risk", "category", "summary", "rate_flags",
                 "version")

    def __init__(self, name, binary, tier, rate, deny_extra, revert, example,
                 risk, category, summary, rate_flags=None, version="w3-1"):
        self.name = name
        self.binary = binary
        self.tier = tier
        self.rate = rate
        # None=未声明（纪律错误），[]=显式空覆盖——构造不抹掉 distinctions
        self.deny_extra = None if deny_extra is None else list(deny_extra)
        self.revert = revert
        self.example = list(example or [])
        self.risk = risk
        self.category = category
        self.summary = summary
        self.rate_flags = list(rate_flags or [])
        self.version = version

    # ---- 纪律字段机械校验（测试=每卡纪律字段完整性）----
    def discipline_errors(self):
        errs = []
        if not self.name or not isinstance(self.name, str):
            errs.append("name 空/非串")
        if not self.binary:
            errs.append("binary 空")
        if self.tier not in TIERS:
            errs.append("tier 不在 %s: %r" % (TIERS, self.tier))
        if not self.rate or not RATE_RE.match(self.rate):
            errs.append("rate 空/非 N/(s|m)|local|serial 形: %r" % self.rate)
        if self.deny_extra is None:
            errs.append("deny_extra 未声明（可为空表，不得 None）")
        if not self.revert or not isinstance(self.revert, str):
            errs.append("revert 义务未显式声明（只读卡=none(只读)，不留空）")
        if not self.example:
            errs.append("example 示例命令缺失")
        elif self.example[0] != self.binary:
            errs.append("example[0] 须=binary: %r" % self.example[0])
        if self.risk not in RISKS:
            errs.append("risk 不在 %s: %r" % (RISKS, self.risk))
        if not self.category:
            errs.append("category 空")
        if not self.summary:
            errs.append("summary 空")
        return errs

    @property
    def requires_approval(self):
        """L3 档=审批门挂卡（未批即拒）。"""
        return self.tier == "L3"

    @property
    def has_revert_obligation(self):
        """none(只读*) 家族=无核销义务（数据用描述性只读变体：只读扫描/只读查询…）。"""
        return not self.revert.startswith(READONLY_PREFIX)

    def as_public_dict(self):
        """清单/详情命令的稳定投影（不含内部路径）。"""
        return {"name": self.name, "binary": self.binary, "tier": self.tier,
                "rate": self.rate, "deny_extra": list(self.deny_extra),
                "revert": self.revert, "example": list(self.example),
                "risk": self.risk, "category": self.category,
                "summary": self.summary, "rate_flags": list(self.rate_flags),
                "version": self.version,
                "requires_approval": self.requires_approval}


# ---- 注册表（模块级单源；import 后 register/unregister 仅供扩展与测试）----
_REGISTRY = {}


def register(card):
    """登记卡：重名=CardError；纪律字段不备=CardError（不完整卡不得入册）。"""
    if card.name in _REGISTRY:
        raise CardError("卡名已注册: " + card.name)
    errs = card.discipline_errors()
    if errs:
        raise CardError("卡 %s 纪律字段不备: %s" % (card.name, "; ".join(errs)))
    _REGISTRY[card.name] = card
    return card


def unregister(name):
    _REGISTRY.pop(name, None)


def get_card(name):
    return _REGISTRY.get(name)


def all_cards():
    return list(_REGISTRY.values())


def card_names():
    return sorted(_REGISTRY)


def _build():
    """蓝图 W3 25 卡落册。档位/限速/revert/reply 示例=RoE 纪律标注（蓝图 58：
    卡带纪律标注）；示例命令主机一律用 target.example 占位（scope 内替换）。"""
    defs = [
        # --- 漏洞扫描组 ---
        ToolCard("nuclei", "nuclei", "L1", "10/s", [],
                 "none(只读扫描)",
                 ["nuclei", "-rl", "10", "-etags", "dos,intrusive",
                  "-u", "https://target.example"],
                 "medium", "vuln-scan", "模板化漏洞扫描（OP1：-rl 限速+dos,intrusive 排除为全局既有执法面）",
                 rate_flags=["-rl"], version="w3-1"),
        ToolCard("testssl", "testssl.sh", "L2", "serial", [],
                 "none(只读探测)",
                 ["testssl.sh", "--quiet", "target.example:443"],
                 "medium", "vuln-scan", "TLS/SSL 配置与证书链体检（串行单连接）"),
        # --- 测绘/侦察组 ---
        ToolCard("nmap", "nmap", "L2", "50/s", ["-T5"],
                 "none(只读扫描)",
                 ["nmap", "--max-rate", "50", "-sV", "-p", "443", "target.example"],
                 "medium", "recon", "端口/服务测绘（受控档：--max-rate 固化，-T5 满速档黑名单拒绝）",
                 rate_flags=["--max-rate"]),
        ToolCard("httpx", "httpx", "L1", "20/s", [],
                 "none(只读探测)",
                 ["httpx", "-u", "https://target.example", "-rate", "20", "-silent"],
                 "low", "recon", "存活/Web 指纹探测", rate_flags=["-rate"]),
        ToolCard("subfinder", "subfinder", "L1", "30/s", [],
                 "none(只读)",
                 ["subfinder", "-rl", "30", "-d", "target.example", "-silent"],
                 "low", "recon", "被动子域发现", rate_flags=["-rl"]),
        ToolCard("katana", "katana", "L1", "10/s", [],
                 "none(只读爬取)",
                 ["katana", "-rl", "10", "-u", "https://target.example", "-d", "3"],
                 "medium", "recon", "爬虫式端点发现（深度受控 -d 3）", rate_flags=["-rl"]),
        ToolCard("dig", "dig", "L1", "20/s", [],
                 "none(只读查询)",
                 ["dig", "+short", "A", "target.example"],
                 "low", "recon", "DNS 记录查询"),
        ToolCard("dnsrecon", "dnsrecon", "L1", "30/s", [],
                 "none(只读查询)",
                 ["dnsrecon", "-d", "target.example", "-t", "std"],
                 "low", "recon", "DNS 区测绘/记录枚举"),
        ToolCard("theHarvester", "theHarvester", "L1", "local", [],
                 "none(只读)",
                 ["theHarvester", "-d", "target.example", "-b", "crtsh"],
                 "low", "osint", "OSINT 公开源信息收集（被动源）"),
        # --- Web 深挖组 ---
        ToolCard("sqlmap", "sqlmap", "L3", "5/s", ["--risk=3", "--level=5"],
                 "输出目录 --purge 核销（--purge-output 痕迹清理义务）",
                 ["sqlmap", "-u", "https://target.example/?id=1", "--batch",
                  "--delay=1", "--risk=1", "--level=1"],
                 "critical", "web", "SQL 注入利用（L3 审批挂卡：未批即拒；满档 risk/level 黑名单拒绝）"),
        ToolCard("ffuf", "ffuf", "L2", "50/s", [],
                 "none(只读枚举)",
                 ["ffuf", "-w", "wordlist.txt", "-u", "https://target.example/FUZZ",
                  "-rate", "50", "-mc", "200"],
                 "medium", "web", "目录/参数模糊测试（限速档：-rate 固化执法）",
                 rate_flags=["-rate"]),
        ToolCard("gobuster", "gobuster", "L2", "50/s", [],
                 "none(只读枚举)",
                 ["gobuster", "dir", "-u", "https://target.example",
                  "-w", "wordlist.txt", "-t", "10"],
                 "medium", "web", "目录/子域爆破（线程受控）"),
        ToolCard("nikto", "nikto", "L2", "10/s", [],
                 "none(只读扫描)",
                 ["nikto", "-h", "https://target.example", "-Tuning", "123bde"],
                 "medium", "web", "Web 服务器已知漏洞扫描"),
        ToolCard("wafw00f", "wafw00f", "L1", "10/s", [],
                 "none(只读探测)",
                 ["wafw00f", "https://target.example"],
                 "low", "web", "WAF 指纹识别"),
        ToolCard("whatweb", "whatweb", "L1", "10/s", [],
                 "none(只读探测)",
                 ["whatweb", "https://target.example"],
                 "low", "web", "Web 技术栈指纹"),
        # --- 横移/内网组（B49：agents 可见面纪律标注）---
        ToolCard("impacket", "impacket-wmiexec", "L3", "local", [],
                 "远端会话与落地文件清理（C$\Admin$ temp 落件核销+会话注销）",
                 ["impacket-wmiexec", "target.example/user:{{vault:cred-N}}"],
                 "critical", "lateral", "内网横移远程执行（L3 审批挂卡：未批即拒；impacket 系执行器）"),
        ToolCard("kerberoast", "impacket-GetUserSPNs", "L2", "local", [],
                 "none(只读请求)",
                 ["impacket-GetUserSPNs", "target.example/", "-request"],
                 "high", "lateral", "Kerberoasting 服务账户哈希离线提取"),
        ToolCard("bloodhound", "bloodhound-python", "L2", "local", [],
                 "none(只读采集)",
                 ["bloodhound-python", "-d", "target.example", "-c", "All"],
                 "high", "lateral", "AD 关系图采集（攻击路径分析）"),
        ToolCard("smbclient", "smbclient", "L2", "local", ["deltree"],
                 "上传/建目录类操作须逐件核销（smb 删改清单对账）",
                 ["smbclient", "//target.example/share", "-N", "-c", "ls"],
                 "medium", "lateral", "SMB 共享访问（deltree 递归删黑名单拒绝）"),
        ToolCard("ldapsearch", "ldapsearch", "L1", "local", [],
                 "none(只读查询)",
                 ["ldapsearch", "-x", "-H", "ldap://target.example",
                  "-b", "dc=target,dc=example"],
                 "low", "lateral", "LDAP 目录查询"),
        ToolCard("redis-cli", "redis-cli", "L2", "local",
                 ["FLUSHALL", "FLUSHDB", "CONFIG SET"],
                 "写键/改配置须逐项核销（键清单对账+CONFIG 还原）",
                 ["redis-cli", "-h", "target.example", "INFO"],
                 "high", "lateral", "Redis 探测（FLUSH*/CONFIG SET 黑名单拒绝）"),
        ToolCard("mysql-client", "mysql", "L2", "local",
                 ["DROP TABLE", "FLUSH PRIVILEGES"],
                 "会话痕迹与所建对象核销（无 DDL 义务时显式记录零残留）",
                 ["mysql", "-h", "target.example", "-u", "ro", "-e", "SELECT VERSION();"],
                 "high", "lateral", "MySQL 客户端（DDL/破坏性语句黑名单拒绝）"),
        # --- 基础设施组 ---
        ToolCard("kubectl", "kubectl", "L2", "local",
                 ["delete", "--all", "delete", "ns", "--force"],
                 "apply/create 所建对象=delete -f 同清单核销（P6.0 清理律）",
                 ["kubectl", "--context", "eng", "get", "pods"],
                 "high", "infra", "K8s 集群只读面+受控变更（delete 全量/强删黑名单拒绝）"),
        ToolCard("curl", "curl", "L1", "10/s", [],
                 "none(只读请求)",
                 ["curl", "-sS", "--max-time", "10", "https://target.example/"],
                 "low", "infra", "HTTP 手工请求（RoE 限速人工自律档）"),
        ToolCard("openssl", "openssl", "L0", "local", [],
                 "none(只读)",
                 ["openssl", "s_client", "-connect", "target.example:443"],
                 "low", "crypto", "证书/TLS 手工体检（本地零流量档）"),
    ]
    for c in defs:
        register(c)


_build()
