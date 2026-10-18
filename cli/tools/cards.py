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

F22 广度补卡 30 张（能力对照总账 §F22 最优方案②）：每卡在七纪律字段之外
另带三件卡面元数据——安装预检命令 install_check（预检 binary 打头，在场+
版本核对；**本仓不装二进制**，装不装点火时人定）/ 版本钉死 pin_version
（预检输出对齐锚；无正式发行版的工具如实标 git-master，不虚构）/ 失败模式
标注 fail_modes（失败方向与处理纪律，防「失败=能力不存在」漏报）。元数据
不入 tools.lock 规范摘要（锁锚=七纪律字段单源，lock.py 零改动）——版本
钉死的执法面=装卡预检输出比对（install.py 在役册），非密码学锚。
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
                 "version", "install_check", "pin_version", "fail_modes")

    def __init__(self, name, binary, tier, rate, deny_extra, revert, example,
                 risk, category, summary, rate_flags=None, version="w3-1",
                 install_check=None, pin_version="", fail_modes=None):
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
        # F22 卡面元数据三件（W3 25 卡缺省=空，不构成纪律字段；F22 卡必带）
        self.install_check = list(install_check or [])
        self.pin_version = str(pin_version or "")
        self.fail_modes = None if fail_modes is None else list(fail_modes)

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
                "install_check": list(self.install_check),
                "pin_version": self.pin_version,
                "fail_modes": list(self.fail_modes or []),
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
                 "远端会话与落地文件清理（C$\\Admin$ temp 落件核销+会话注销）",
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


def _build_f22():
    """F22 广度补卡 30 张落册（§F22 最优方案②：参照 CSAI 90 卡清单选高频
    +补 GT L4 容器/云空白）。纪律：七字段全带+安装预检+版本钉死+失败模式
    标注；**不装二进制**（装不装点火时人定——预检命令在卡面，装卡=
    tanyin-tools install 走验签在役册）。清单外剔除记录：qsx/mediate 无
    公开可信发行面（不虚构卡面，报账在案）。"""
    defs = [
        # --- 容器/云（GT L4 空白直补）---
        ToolCard("trivy", "trivy", "L1", "local", [],
                 "none(只读扫描)",
                 ["trivy", "image", "--scanners", "vuln",
                  "--severity", "HIGH,CRITICAL", "nginx:1.27"],
                 "medium", "container",
                 "镜像/文件系统漏洞扫描（容器面 GT L4 直补；不装二进制，预检点火）",
                 version="f22-1",
                 install_check=["trivy", "--version"], pin_version="0.58.1",
                 fail_modes=["DB 未初始化→首跑需联网下载漏洞库（离线预检失败）",
                             "镜像不在本地→先 docker pull 或给 tar 包路径",
                             "JSON 输出超大→执行器 spill 件兜底不进上下文"]),
        ToolCard("checkov", "checkov", "L1", "local", [],
                 "none(只读扫描)",
                 ["checkov", "-f", "iac.tf", "--framework", "terraform",
                  "--quiet"],
                 "medium", "container", "IaC 配置错误扫描（terraform/k8s/云）",
                 version="f22-1",
                 install_check=["checkov", "--version"], pin_version="3.2.227",
                 fail_modes=["Python 依赖冲突→pipx 隔离安装预检",
                             "框架识别失败→显式 --framework 传入",
                             "基线误报→逐条带 check id 入账可复核"]),
        ToolCard("kube-bench", "kube-bench", "L1", "local", [],
                 "none(只读扫描)",
                 ["kube-bench", "run", "--benchmark", "cis-1.8"],
                 "medium", "container", "CIS 基准 K8s 节点体检",
                 version="f22-1",
                 install_check=["kube-bench", "version"], pin_version="0.10.0",
                 fail_modes=["节点缺 kubelet 配置路径→如实记无信号",
                             "benchmark 版本与集群不符→对照 CIS 版本表重指",
                             "容器内运行缺宿主挂载→hostPath 预检清单"]),
        ToolCard("kube-hunter", "kube-hunter", "L2", "serial", ["--active"],
                 "none(只读探测)",
                 ["kube-hunter", "--remote", "cluster.example"],
                 "high", "container",
                 "集群远程猎洞（被动面；--active 主动利用档黑名单拒绝）",
                 version="f22-1",
                 install_check=["kube-hunter", "--version"],
                 pin_version="0.7.1",
                 fail_modes=["远程不可达→网络分段事实入账",
                             "--active 主动档须 RoE 重批（黑名单挡）",
                             "凭证面发现→只走 vault 不进上下文"]),
        # --- 凭据攻击/横移毒化（L3 审批挂卡）---
        ToolCard("hydra", "hydra", "L3", "serial", [],
                 "恢复文件 .hydra.restore 与输出文件核销（清单对账）",
                 ["hydra", "-L", "users.txt", "-P", "passes.txt", "-t", "4",
                  "-W", "3", "ssh://target.example"],
                 "critical", "lateral",
                 "在线口令攻击（L3 审批挂卡：凭据攻击执行未批即拒；-t 受控）",
                 version="f22-1",
                 install_check=["hydra", "-h"], pin_version="9.5",
                 fail_modes=["目标锁定账户→RoE 授权账户清单核对",
                             "-t 过高触发封禁→默认 -t 4 受控档",
                             "restore 残留→收工核销 .hydra.restore"]),
        ToolCard("krbrelayx", "krbrelayx", "L3", "local", [],
                 "中继监听停止+落地 SMB 文件核销（清单对账）",
                 ["krbrelayx", "-hashes", ":{{vault:cred-N}}"],
                 "critical", "lateral",
                 "Kerberos 中继（L3 审批挂卡：凭据攻击执行未批即拒）",
                 version="f22-1",
                 install_check=["krbrelayx", "--help"],
                 pin_version="git-master（无正式发行版）",
                 fail_modes=["需受害端主动认证触发→无回调=无信号如实记",
                             "SMB 签名强制启用→relay 不可行转记事实",
                             "监听端口占用→预检 445/80 空闲"]),
        ToolCard("impacket-secretsdump", "impacket-secretsdump", "L3",
                 "local", [],
                 "none(只读提取)",
                 ["impacket-secretsdump", "target.example/user:{{vault:cred-N}}"],
                 "critical", "lateral",
                 "域凭据材料提取（L3 审批挂卡：凭据攻击执行未批即拒）",
                 version="f22-1",
                 install_check=["impacket-secretsdump", "--help"],
                 pin_version="impacket-0.12.0",
                 fail_modes=["凭据失效→STATUS_LOGON_FAILURE 不重试超 RoE",
                             "SYSVOL 不可达→网络分段事实入账",
                             "输出含凭据材料→只走 vault 通道不进上下文"]),
        ToolCard("impacket-getst", "impacket-getST", "L3", "local", [],
                 "none(只读请求)",
                 ["impacket-getST", "-spn", "cifs/target.example",
                  "-impersonate", "user",
                  "target.example/user:{{vault:cred-N}}"],
                 "critical", "lateral",
                 "服务票据请求/银票据锻造（L3 审批挂卡：凭据攻击执行）",
                 version="f22-1",
                 install_check=["impacket-getST", "--help"],
                 pin_version="impacket-0.12.0",
                 fail_modes=["SPN 不存在→先 Kerberoast 确认 SPN",
                             "时钟偏移>5min→票据无效（NTP 预检）",
                             "生成 .ccache 落地→收工核销文件"]),
        ToolCard("impacket-ticketer", "impacket-ticketer", "L3", "local", [],
                 "生成的票据文件核销（.ccache/.kirbi 清单对账）",
                 ["impacket-ticketer", "-nthash", "{{vault:cred-N}}",
                  "-domain-sid", "S-1-5-21-x", "-domain", "target.example",
                  "user"],
                 "critical", "lateral",
                 "黄金/白银票据伪造（L3 审批挂卡：凭据攻击执行未批即拒）",
                 version="f22-1",
                 install_check=["impacket-ticketer", "--help"],
                 pin_version="impacket-0.12.0",
                 fail_modes=["domain-sid 错→票据拒收（先取准 SID）",
                             "密钥版本/加密选型不符→KRB_AP_ERR_MODIFIED",
                             "票据文件残留→核销清单对账"]),
        ToolCard("responder", "responder", "L3", "serial", ["-F"],
                 "毒化监听停止+捕获哈希只走 vault+落盘日志核销",
                 ["responder", "-I", "en0"],
                 "critical", "lateral",
                 "LLMNR/NBT-NS 毒化凭据捕获（L3 审批挂卡；-F 强制档黑名单拒）",
                 version="f22-1",
                 install_check=["responder", "--version"],
                 pin_version="3.1.4.0",
                 fail_modes=["须独占网络位→RoE 授权网络段核对",
                             "捕获哈希只进 vault 不进上下文",
                             "与 mitm6 同段互扰→预检无其他毒化器在飞"]),
        ToolCard("mitm6", "mitm6", "L3", "local", [],
                 "流氓 DHCPv6 停止+DNS 劫持记录核销",
                 ["mitm6", "-d", "target.example"],
                 "critical", "lateral",
                 "IPv6 DNS 劫持（L3 审批挂卡：横移毒化未批即拒）",
                 version="f22-1",
                 install_check=["mitm6", "--help"], pin_version="2.2.0",
                 fail_modes=["网段无 IPv6→无信号如实记",
                             "与 responder 联动须先停其 DNS 模块防互扰",
                             "RA Guard 拦截→劫持失效记事实"]),
        ToolCard("ettercap", "ettercap", "L3", "serial", [],
                 "ARP 毒化表还原（统一 ARP 广播净化）+嗅探落盘核销",
                 ["ettercap", "-T", "-q", "-M", "arp:remote",
                  "/target.example//"],
                 "critical", "lateral",
                 "中间人/ARP 毒化（L3 审批挂卡：横移未批即拒；静默档）",
                 version="f22-1",
                 install_check=["ettercap", "--version"],
                 pin_version="0.8.3.1",
                 fail_modes=["交换机端口安全/DAI→毒化失败如实记",
                             "HSTS 下 SSL 剥离多失效→预期降档",
                             "双向流量风暴→-Tq 静默档+时长帽"]),
        # --- 横移探测（L2 面：破坏性旗标黑名单拒绝）---
        ToolCard("netexec", "netexec", "L2", "serial",
                 ["--sam", "--lsa", "-x", "--exec-method"],
                 "none(只读探测)",
                 ["netexec", "smb", "target.example", "-u", "user",
                  "-p", "{{vault:cred-N}}", "--shares"],
                 "high", "lateral",
                 "内网协议测试套（SMB/WinRM/LDAP；凭据转储/远程执行旗标黑名单拒）",
                 version="f22-1",
                 install_check=["netexec", "--version"], pin_version="1.5.0",
                 fail_modes=["凭据失效→STATUS_LOGON_FAILURE 不重试超 RoE",
                             "SMB 签名强制→NTLM relay 不可行记事实",
                             "协议选错(smb/winrm/ldap)→端口预检"]),
        ToolCard("crackmapexec", "crackmapexec", "L2", "serial",
                 ["--sam", "--lsa", "-x", "--exec-method"],
                 "none(只读探测)",
                 ["crackmapexec", "smb", "target.example", "-u", "user",
                  "-p", "{{vault:cred-N}}", "--shares"],
                 "high", "lateral",
                 "内网协议测试套（netexec 前身；遗留环境面，凭据转储/远程执行旗标黑名单拒）",
                 version="f22-1",
                 install_check=["crackmapexec", "--version"],
                 pin_version="5.4.0",
                 fail_modes=["上游停更归档→新仗优先 netexec 卡",
                             "凭据失效不重试超 RoE",
                             "输出含凭据回显→脱敏入账"]),
        ToolCard("dsquery", "dsquery", "L1", "local", [],
                 "none(只读查询)",
                 ["dsquery", "user", "-name", "adm*", "-limit", "100"],
                 "low", "lateral",
                 "AD 目录查询（Windows 域控侧 builtin；Linux 侧走 ldapsearch 卡）",
                 version="f22-1",
                 install_check=["dsquery", "user", "-limit", "1"],
                 pin_version="windows-builtin（域控 2012R2+）",
                 fail_modes=["仅 Windows 域控侧可跑→执行后端 OS 预检",
                             "须域凭据→vault 通道",
                             "输出超限→执行器 spill 件兜底"]),
        # --- Web 深挖 ---
        ToolCard("feroxbuster", "feroxbuster", "L2", "50/s", [],
                 "none(只读枚举)",
                 ["feroxbuster", "-u", "https://target.example",
                  "-w", "wordlist.txt", "--rate-limit", "50", "-d", "2"],
                 "medium", "web", "目录/端点递归爆破（--rate-limit 固化执法）",
                 rate_flags=["--rate-limit"], version="f22-1",
                 install_check=["feroxbuster", "--version"],
                 pin_version="2.10.1",
                 fail_modes=["递归深度失控→-d 2 固化",
                             "软 404 误报→--auto-tune 校准",
                             "输出巨量→spill 件兜底"]),
        ToolCard("arjun", "arjun", "L1", "serial", [],
                 "none(只读探测)",
                 ["arjun", "-u", "https://target.example/api", "-m", "GET"],
                 "low", "web", "隐藏参数发现（GET/POST/JSON 多法探测）",
                 version="f22-1",
                 install_check=["arjun", "--version"], pin_version="2.2.7",
                 fail_modes=["WAF 拦截→429/403 记事实降档",
                             "JSON/XML 体须 -cT 指定内容型",
                             "大参数表超时→--stable 档"]),
        ToolCard("jwt-tool", "jwt_tool", "L2", "serial", [],
                 "none(只读探测)",
                 ["jwt_tool", "eyJhbGciOiJub25lIn0.e30.", "-M", "at"],
                 "medium", "web", "JWT 分析/篡改/弱签测试（alg 混淆面）",
                 version="f22-1",
                 install_check=["jwt_tool"], pin_version="2.2.6",
                 fail_modes=["盲重放浪费→先 httprobe 存活",
                             "弱签字典跑→时长帽",
                             "篡改报文逐条入证据卡（EV 卡 raw_request）"]),
        ToolCard("dirsearch", "dirsearch", "L2", "50/s", [],
                 "none(只读枚举)",
                 ["dirsearch", "-u", "https://target.example",
                  "-w", "wordlist.txt", "-t", "10"],
                 "medium", "web", "目录/路径爆破（线程受控）",
                 version="f22-1",
                 install_check=["dirsearch", "-h"], pin_version="0.4.3",
                 fail_modes=["扩展名组合爆炸→-e 白名单",
                             "递归失控→默认不递归",
                             "软 404 误报→对照页校准"]),
        ToolCard("kiterunner", "kr", "L2", "50/s", [],
                 "none(只读枚举)",
                 ["kr", "scan", "https://target.example",
                  "-w", "routes-small.kite"],
                 "medium", "web", "API 路由枚举（kite 字典；非标路由框架利器）",
                 version="f22-1",
                 install_check=["kr", "version"], pin_version="1.0.2",
                 fail_modes=["大字典流量高→routes-small 起步",
                             "非标框架误报多→对 whatweb 指纹",
                             "404 语义混淆→--fail-status 校准"]),
        # --- 测绘/侦察 ---
        ToolCard("httprobe", "httprobe", "L1", "50/s", [],
                 "none(只读探测)",
                 ["httprobe", "-c", "20", "-p", "https:443"],
                 "low", "recon", "子域存活探测（stdin 驱动批量面）",
                 version="f22-1",
                 install_check=["httprobe"],
                 pin_version="git-master（无正式发行版）",
                 fail_modes=["stdin 驱动→上游子域清单先就位",
                             "双 scheme 试探→结果带 scheme 入账",
                             "401/403≠死链（活着但守门）"]),
        ToolCard("gau", "gau", "L1", "serial", [],
                 "none(只读查询)",
                 ["gau", "--threads", "5", "--o", "urls.txt",
                  "target.example"],
                 "low", "recon", "URL 归档聚合（wayback/commoncrawl/otrx 三源）",
                 version="f22-1",
                 install_check=["gau", "--version"], pin_version="2.2.4",
                 fail_modes=["归档 API 限流→退避+如实记部分结果",
                             "URL 巨量→落盘+spill 兜底不进上下文",
                             "失效 URL 占比高→httprobe 复活过滤"]),
        ToolCard("waybackurls", "waybackurls", "L1", "serial", [],
                 "none(只读查询)",
                 ["waybackurls", "target.example"],
                 "low", "recon", "Wayback CDX 历史 URL 拉取",
                 version="f22-1",
                 install_check=["waybackurls"],
                 pin_version="git-master（无正式发行版）",
                 fail_modes=["CDX 不可用→失败如实记无信号",
                             "输出巨量→落盘+spill 兜底",
                             "历史 URL 未复活→只作候选面"]),
        ToolCard("masscan", "masscan", "L2", "50/s", [],
                 "none(只读扫描)",
                 ["masscan", "-p", "443,80", "--rate", "50",
                  "10.10.0.0/24"],
                 "medium", "recon",
                 "高速端口测绘（--rate 固化执法；SYN 扫描须 root）",
                 rate_flags=["--rate"], version="f22-1",
                 install_check=["masscan", "--version"], pin_version="1.3.2",
                 fail_modes=["--rate 缺旗标即拒（gate 固化）",
                             "出网 ACL 段预检（错段=全网骚扰）",
                             "SYN 扫描 root 权限缺失→权限预检"]),
        ToolCard("rustscan", "rustscan", "L2", "50/s", [],
                 "none(只读扫描)",
                 ["rustscan", "-a", "target.example", "-p", "443",
                  "-t", "3000"],
                 "medium", "recon", "高速端口扫描（现代 nmap 前置）",
                 version="f22-1",
                 install_check=["rustscan", "--version"],
                 pin_version="2.3.0",
                 fail_modes=["默认链 nmap 联动→裸扫或 RoE 明示",
                             "ulimit 文件帽→批量目标预检",
                             "UDP 不支持→仅 TCP 面"]),
        ToolCard("naabu", "naabu", "L2", "50/s", [],
                 "none(只读扫描)",
                 ["naabu", "-host", "target.example", "-p", "1-1000",
                  "-rate", "50", "-silent"],
                 "medium", "recon", "端口扫描（-rate 固化执法；SYN 须 root）",
                 rate_flags=["-rate"], version="f22-1",
                 install_check=["naabu", "-version"], pin_version="2.3.2",
                 fail_modes=["SYN 扫描须 root→权限预检",
                             "CDN 全开假象→对照 dnsx 解析归一",
                             "-rate 缺旗标即拒（gate 固化）"]),
        ToolCard("dnsx", "dnsx", "L1", "50/s", [],
                 "none(只读查询)",
                 ["dnsx", "-d", "target.example", "-silent"],
                 "low", "recon", "DNS 解析/反查/记录枚举（批量面）",
                 version="f22-1",
                 install_check=["dnsx", "-version"], pin_version="1.2.3",
                 fail_modes=["解析链超时→重试帽+记无信号",
                             "泛解析域名→cname 归一对照",
                             "输出巨量→spill 兜底"]),
        ToolCard("amass", "amass", "L1", "serial", ["-brute"],
                 "none(只读枚举)",
                 ["amass", "enum", "-passive", "-d", "target.example"],
                 "medium", "recon",
                 "深度子域测绘（被动面；-brute 主动爆破档黑名单拒）",
                 version="f22-1",
                 install_check=["amass", "-version"], pin_version="4.2.0",
                 fail_modes=["数据源 API 键未配→被动结果部分降级如实标",
                             "运行时长长→执行器异步件兜底不占轮次",
                             "第三方情报→来源标注入账"]),
        # --- vuln-scan 补件 ---
        ToolCard("sslscan", "sslscan", "L1", "serial", [],
                 "none(只读探测)",
                 ["sslscan", "--no-failed", "target.example:443"],
                 "low", "vuln-scan", "TLS/SSL 密码套件与证书快检",
                 version="f22-1",
                 install_check=["sslscan", "--version"],
                 pin_version="2.1.2",
                 fail_modes=["STARTTLS 服务须 --starttls-<proto> 指定",
                             "套件列表超长→--no-failed 收敛",
                             "超时重试帽+记无信号"]),
        ToolCard("nuclei-templates", "nuclei", "L1", "local", [],
                 "none(只读本机安装面更新)",
                 ["nuclei", "-update-templates", "-silent"],
                 "low", "vuln-scan",
                 "模板包更新（nuclei 卡配套；本机安装面零战场副作用）",
                 version="f22-1",
                 install_check=["nuclei", "-version"], pin_version="v10.0.0",
                 fail_modes=["更新走网络下载→离线环境预检失败",
                             "模板包体量大→磁盘帽预检",
                             "nuclei 主程序与模板 tag 兼容面核对"]),
    ]
    for c in defs:
        register(c)


_build()
_build_f22()
