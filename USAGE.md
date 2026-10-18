# 探隐 TanYin · 使用指导（USAGE）

> 一人红队 AI 自动化渗透平台。运行时无关（DSH / opencode / codex），账本为法，技能为术，引擎为骨。

## 零、opencode 模型配置（异地跑战士前置，2026-10-11 补）

**项目配置随仓走**（权限面）；**模型/供应商在全局配置**（不在仓内，含 key 不入库）：

`~/.config/opencode/opencode.json` 最小可用块：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "zhipuai-coding-plan": { "options": { "apiKey": "<您的 bigmodel key>" } }
  },
  "model": "zhipuai-coding-plan/glm-5.3",
  "small_model": "zhipuai-coding-plan/glm-5-turbo"
}
```

- **指定模型两法**：① 配置文件 `model` 字段设默认（battle.py 走这个）；② 手动跑时显式指定：`python3 cli/tanyin-runner start ... --model zhipuai-coding-plan/glm-5.3`（runner 转发 `opencode run --model`）。
- **thinking 参数**：本平台未单独调 —— glm-5.3 经 coding-plan 端点推理默认开；若供应商列出思考变体名（如 `.../glm-5.3-thinking`），`opencode models` 可查全部可选名，按名指定即可。
- 验证：`opencode run -m zhipuai-coding-plan/glm-5.3 "回一个 OK"` 出字=链路通。

## 一、新电脑安装（一次性，约 2 分钟）

```bash
# 前提：git、python3（Mac/Linux 自带；零 pip 依赖）。AI 战士需 opencode+模型 key。
git clone https://github.com/Wgen1995/redteam-agent.git
cd redteam-agent
python3 cli/tanyin-ledger --help    # 出命令列表 = 安装成功
```

- 打真实目标：**不需要 Docker**（出网管控=纯 Python 的 tanyin-egress/tanyin-guard）
- 跑训练靶场/复现战报：需要 Docker

## 一·五、参数速查表（2026-10-11 补）

### tanyin-runner start —— 引擎托管（14 参数）

| 参数 | 必填 | 默认 | 作用 |
|---|---|---|---|
| --cwd | ✓ | — | 作战目录 |
| --prompt-file | ✓ | — | 任务书（八问答案形） |
| --log | ✓ | — | 战士主日志 |
| --ledger-dir | ✓ | — | 账本目录 |
| --model | | None=opencode 默认 | 指定模型（供应商/型号） |
| --max-restarts | | 5 | 死亡续跑上限 |
| --stall-min | | 8.0 | 硬击杀阈值（分钟） |
| --soft-stall-min | | 3.0 | 软停滞观察阈值（分钟） |
| --backoff-base | | 30 | 重启退避基秒（×4ⁿ 封顶 480） |
| --directive-file | | None | 战中指令控制文件（digest 变→带令续跑） |
| --ask-file | | None | ask:human 问答通道文件 |
| --tick-sec | | 30 | 心跳轮询周期（秒） |
| --runner-log | | None | 看门狗自身日志 |
| --caffeinate | | off | 防系统休眠 |

### battle.py —— 靶场连战（4 子命令）

```bash
init    --n 26 --gen G-r27 [--brief 战书模板] [--boot-mode agent|det] [--dry-run]
launch  --n 26 --gen G-r27 [--max-restarts 5] [--stall-min 8] [--soft-stall-min 3]
                       [--backoff-base 30] [--caffeinate]   # runner 参数透传同上表
watch   --n 26 --gen G-r27    # 实时进度，Ctrl-C 不影响战局
settle  --n 26 --gen G-r27    # 战毕评分（56 分母召回+链验证）
```

--n=战号  --gen=世代号；首跑只碰 init/launch/settle 三个，其余全默认即战级配置。


## 二、开战（每次）

### 方式 1 · 引擎托管（推荐——无人值守）

```bash
python3 cli/tanyin-runner start --cwd $(pwd) \
  --prompt-file my-mission.txt \
  --log ~/.tanyin/runs/run1.log --ledger-dir sessions/G-x1
```

> 数据持久化：默认家 `~/.tanyin`（`TANYIN_HOME` 可覆盖）——**别放 /tmp，重启即失**。Windows 下全部命令 `py -3` 等价，battle.py/runner 已去 POSIX 依赖。

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

`SKILL.md`（总控路由器）｜`cli/README.md`（55 命令，计数单源=docs/counts.json）｜`contracts/`（15 合约）｜`docs/HANDOFF.md`（22 战全记录+飞轮）
