# 探隐 TanYin · 一人红队 AI 自动化渗透平台

> 账本为法，技能为术，引擎为骨，插件为面。运行时无关（DSH / opencode / codex），macOS/Linux/Windows 三平台。

AI 战士按九门流程（P0 授权门→P1 测绘→P2 规划→P3 演进→P4 重放验证→P5 签发）对授权目标作战，每个发现都有可重放证据卡，全程账本留痕防篡改。

**训练靶场战绩**（56 分母召回，同战士 opencode+GLM-5.3）：战书 30 面配置 **0.66** 稳定最优；单样本峰值 0.70（复现实验证伪其稳定性，见 `knowledge/retros/RT-0023.md`）。

## 一、下载

```bash
git clone https://github.com/Wgen1995/redteam-agent.git
cd redteam-agent
```

| 组件 | 前提 | 用途 |
|---|---|---|
| 账本+引擎 | git + python3（3.10+，零 pip 依赖） | 必装核心 |
| AI 战士 | [opencode](https://opencode.ai) + 模型 key（默认 zhipuai） | 自动渗透 |
| 训练靶场 | Docker + docker compose | 可选（打真实目标不需要） |
| DSH 插件 | Node 20+ + dsh CLI | 可选（把账本当原生工具用） |

## 二、安装（一次性，约 2 分钟）

```bash
python3 cli/tanyin-ledger --help    # 出命令用法 = 核心安装成功
```

- 数据家：`~/.tanyin`（环境变量 `TANYIN_HOME` 可覆盖）——**别放 /tmp，重启即失**
- Windows：全部命令 `py -3` 等价（仓已去 POSIX 依赖，UTF-8/LF 强制）
- AI 战士的 opencode 权限预配在 `.opencode/opencode.json`（仓里自带）；技能在 `.opencode/skills/tanyin/`

## 三、运行（四种方式）

### 方式 1 · 引擎托管（无人值守，推荐）

写好任务书（P0 授权八问的答案直接给出）→ 引擎自动心跳监控/停滞击杀/死亡续跑：

```bash
python3 cli/tanyin-runner start --cwd $(pwd) \
  --prompt-file my-mission.txt \
  --log ~/.tanyin/runs/run1.log --ledger-dir sessions/G-x1
```

任务书模板（八问答案形）见 `USAGE.md` 第二节。

### 方式 2 · 靶场连战（battle.py——训练/回归专用）

对内置 8 服务靶场发起全自动战，战毕自动判据（`gate-exit:P4`）、评分、金样回归：

```bash
docker compose -f tests/range/docker-compose.yml up -d   # 起靶场（首次）
python3 scripts/battle.py init   --n 26 --gen G-r27      # 建战局+任务书（场景钟自动推）
python3 scripts/battle.py launch --n 26 --gen G-r27      # 点火（runner 托管+心跳+续跑）
python3 scripts/battle.py watch  --n 26 --gen G-r27      # 实时看进度（Ctrl-C 退出不影响战局）
python3 scripts/battle.py settle --n 26 --gen G-r27      # 战毕评分（56 分母召回）
```

战局数据在 `~/.tanyin/battles/battle-26/`；历史金样 `tests/fixtures/G-r*/`（钉测回归防键控漂移）。

### 方式 3 · 直接对话（有人在环）

```bash
cd redteam-agent && opencode
# 输入：用 tanyin 技能，对 <目标> 开战，授权书是 <路径>
```

AI 反问八问 → 全自动 P0→P4 → P5 签发门停下等人审。

### 方式 4 · 干跑自检（零对外请求）

对 AI 说：「用 tanyin 技能，干跑模式自检」。

## 四、DSH 插件（可选——账本当原生工具）

把 13 个高频账本命令铸成 3 个带类型的安全工具（`tanyin_book` 写令 7 / `tanyin_gate` 门令 3 / `tanyin_query` 查令 3），schema 描述即作战纪律（scope 联查/一洞一行写进工具说明，模型调用前就见到法）：

```bash
# 安装进 dsh 的 default profile（本地路径直装，未发 npm）
dsh plugin --profile default add file:$(pwd)/platform/dsh-plugin-tanyin

# 验证层已挂（应见 '# == dsh-plugin-tanyin' 条目）
dsh --profile default --dump-config | grep -A2 tanyin

# 单测（4 件：注册/白名单拒越界/输出信封/无幻影命令）
cd platform/dsh-plugin-tanyin && npm install && npm test
```

之后任何 `dsh` 会话（default profile 启动）模型即可直接调三工具操账本。**注意**：首次真用需要 DSH 账户有余额（余额不足时 headless 冒烟会报 `QUOTA: Insufficient Balance`）。

## 五、成果在哪

```
sessions/<任务>/            # 打真实目标
~/.tanyin/battles/battle-N/  # 靶场战局
├── findings.tsv    漏洞清单（交付物）
├── E-index.tsv     证据卡（每个洞可重放验证）
└── timeline.tsv    全程审计链（防篡改哈希链）
```

整个目录=交付物。验收：`python3 cli/tanyin-ledger validate --goal-dir <会话目录>`。

## 六、训练与度量

```bash
python3 tests/eval_range_recall.py --session <会话> \
  --ground-truth tests/range/ground-truth.json    # 56 分母召回评分（键控 v7）
python3 -m unittest discover tests -q              # 全套件（含历代金样钉测）
```

## 七、常见问题（实战血泪）

| 问题 | 答案 |
|---|---|
| opencode 非交互权限被拒 | 项目级 `.opencode/opencode.json` 已预配；**战士禁用裸 /tmp 路径**（权限墙杀会话，任务书已带补令） |
| 会话中途死了 | 引擎自动续跑（状态在盘）；网络断流→停滞击杀→自动重启，账本零损 |
| 假完成（rc=0 但没打完） | runner 战毕判据=`gate-exit:P4`，不是 rc=0——battle.py 已内置 |
| DSH headless 报 QUOTA | 账户充值即可；boot 与插件加载不受影响 |
| Windows | `py -3 scripts\battle.py init --n 26 --gen G-r27` 等价 |

## 八、文档地图

- `USAGE.md` —— 使用指导（任务书模板/四方式细节/FAQ）
- `docs/HANDOFF.md` —— 交接全录（历代战报与工程决策）
- `knowledge/retros/RT-*.md` —— 复盘飞轮（每战必复盘）
- `platform/dsh-plugin-tanyin/README.md` —— 插件开发面

---

**授权前提**：本平台仅对书面授权范围内的目标作业。训练靶场（`tests/range/`）为合成环境，信标带 `GT*` 前缀可审计。
