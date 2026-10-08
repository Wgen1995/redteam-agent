# 探隐 TanYin · 使用指导（USAGE）

> 一人红队 AI 自动化渗透平台。运行时无关（DSH / opencode / codex），账本为法，技能为术，引擎为骨。

## 一、新电脑安装（一次性，约 2 分钟）

```bash
# 前提：git、python3（Mac/Linux 自带；零 pip 依赖）。AI 战士需 opencode+模型 key。
git clone https://github.com/Wgen1995/redteam-agent.git
cd redteam-agent
python3 cli/tanyin-ledger --help    # 出命令列表 = 安装成功
```

- 打真实目标：**不需要 Docker**（出网管控=纯 Python 的 tanyin-egress/tanyin-guard）
- 跑训练靶场/复现战报：需要 Docker

## 二、开战（每次）

### 方式 1 · 引擎托管（推荐——无人值守）

```bash
python3 cli/tanyin-runner start --cwd $(pwd) \
  --prompt-file my-mission.txt \
  --log run.log --ledger-dir sessions/G-x1
```

`my-mission.txt` 写法（P0 授权八问的答案直接给出，避免交互）：

```
使用 tanyin 技能（.opencode/skills/tanyin/SKILL.md），对本授权目标执行完整渗透。
1) 目标：<IP/域名>  2) 授权文件：<路径+sha256>  3) 窗口：<起止时间>
4) 范围：include/exclude/oob  5) 预算：2M;50000;40  6) 凭据：<无/预发>
7) 强度：禁 DoS；探测经 <通道>  8) 会话目录：sessions/G-x1
```

引擎自动：心跳监控 → 停滞击杀 → 死亡续跑（恢复协议内置）。

### 方式 2 · 直接对话（有人在环）

```bash
cd redteam-agent && opencode
# 输入：用 tanyin 技能，对 <目标> 开战，授权书是 <路径>
```

AI 反问八问 → 全自动 P0→P4 → 签发门停下等您人审。

### 方式 3 · 干跑自检（零对外请求）

对 AI 说：「用 tanyin 技能，干跑模式自检」。

## 三、成果在哪

```
sessions/<任务>/
├── findings.tsv    漏洞清单（交付物）
├── E-index.tsv     证据卡（每个洞可重放验证）
└── timeline.tsv    全程审计链（防篡改）
```

整个目录=交付物。验收：`python3 cli/tanyin-ledger validate --goal-dir sessions/<任务>`。

## 四、训练与度量（可选）

```bash
docker compose -f tests/range/docker-compose.yml up -d     # 8 服务靶场
python3 tests/eval_range_recall.py --session <会话> \
  --ground-truth tests/range/ground-truth.json             # 56 分母召回评分
```

## 五、常见问题

| 问题 | 答案 |
|---|---|
| opencode 非交互权限被拒 | 项目级 .opencode/opencode.json 预放权限（仓里已带）或用方式 1 引擎 |
| 会话中途死了 | 方式 1 会自动续跑；手工续：`opencode run -c "继续"` |
| Windows | `py -3 cli\tanyin-ledger ...`（见 cli/README.md） |
| 模型 | 默认读 opencode 配置；引擎可 --model 覆盖 |

## 六、深入学习

`SKILL.md`（总控路由器）｜`cli/README.md`（44 命令）｜`contracts/`（15 合约）｜`docs/HANDOFF.md`（22 战全记录+飞轮）
