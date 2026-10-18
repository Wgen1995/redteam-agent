# 首仗操作单 —— 五步:起服 → 建仗 → 灌道 → 点火 → 判卷

给谁看:第一次真打仗的操作员(人或 AI 副驾)。读完能从零把一场真仗跑完。
一句话版本:**前四步全部免费、零外部 API 调用;只有第四步「点火」真花钱,
而且必须由用户点头后才执行。** 判卷不看过程辛苦,只看真找到了哪些漏洞。

目录里已经备好的三样东西:

| 东西 | 位置 | 是什么 |
|---|---|---|
| 演示战役 DEMO-1 | `demos/DEMO-1/` | 111 条发现 + 709 行时间线的完整战账(拷自金样 G-r18),账本长什么样先看它 |
| 模型道样例 | `cli/warrior/channels.example.json` | 真模型道的样子,真钥匙已脱敏,照抄改钥即用 |
| 本操作单 | `docs/FIRST-BATTLE-RUNBOOK.md` | 你在读的这份 |

---

## 第一步 · 起服(把靶场立起来,免费)

靶场 = ZhuLong 平台(本机另一个仓,只读,不许改它源码)。它默认写 `data/`
目录、默认端口 7090,我们都换掉:数据指到 /tmp,服务听 3081,只听本机。

```bash
# 一次性准备:让服务只听 127.0.0.1(ZhuLong 仓只读改不了源码,用这个注入)
cat > /tmp/zl-loopback-shim.cjs <<'EOF'
const http = require('http');
const ALL_IF = new Set([undefined, null, '', '::', '0.0.0.0']);
const orig = http.Server.prototype.listen;
http.Server.prototype.listen = function (...args) {
  if (typeof args[0] === 'number' && ALL_IF.has(args[1]))
    return orig.call(this, args[0], '127.0.0.1', ...args.slice(2));
  return orig.apply(this, args);
};
EOF

# 起服务(在 ZhuLong 仓根目录;数据全进 /tmp,仓保持只读)
cd "/Users/wgen/Documents/AI For Security & Compliance/ai-assisted-security-verification-platform"
NODE_OPTIONS="--require /tmp/zl-loopback-shim.cjs" \
  ZL_PORT=3081 ZL_DATA_DIR=/tmp/zl-demo-data \
  pnpm --filter @zhulong/server start        # 后台跑,别占着终端

# 验活:这两条通了就是活了
curl http://127.0.0.1:3081/api/health        # 期望 {"ok":true,"db":"ok",...}
lsof -nP -iTCP:3081 -sTCP:LISTEN             # 期望看到 127.0.0.1:3081(不是 0.0.0.0)
```

第一次起(用户表是空的)要先建第一个管理员,然后试登录:

```bash
curl -X POST http://127.0.0.1:3081/api/setup \
  -H 'Content-Type: application/json' \
  -d '{"username":"你的名字","password":"定个密码"}'      # 只许成功一次

curl -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:3081/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"你的名字","password":"定个密码"}'      # 期望 200
```

想在浏览器里看登录页(可选):

```bash
ZL_DEV_API_TARGET=http://127.0.0.1:3081 \
  pnpm --filter @zhulong/web exec vite --port 3082 --host 127.0.0.1
# 浏览器开 http://127.0.0.1:3082/login —— 标题应为「烛龙 ZhuLong」
```

注意端口纪律:**8900 / 3000 / 8787 / 8443 是保留口**(8900 是操作台常驻面),
哪个服务都别去占。3081 是靶场、3082 是靶场登录页,按本单用。

## 第二步 · 建仗(立军令状,免费)

- **演示/教学**:直接用现成的 `demos/DEMO-1`,一分钟验收:
  ```bash
  python3 cli/tanyin-ledger verify-chain --goal-dir demos/DEMO-1
  # 期望: PASS verify-chain: 709 行链完整 gate_exit=5 跳门=0
  ```
- **真仗**:新建战役目录(默认在 `~/.tanyin/battles/battle-N`,可用 `TANYIN_HOME`
  环境变量改地方)。两条路:
  - 有操作台(8900 已在跑就别再起一个):页面上「新建任务」;
  - 命令行:`python3 scripts/battle.py init --n 1 --brief "首场真仗"`
    (注意:它现在按 docker 靶场默认写范围;打 ZhuLong 3081 就建完后用
    `add-goal`/`add-scope` 把目标和范围改成 `127.0.0.1:3081`)。

## 第三步 · 灌道(接真模型,免费,但别把钥匙提交进 git)

```bash
cp cli/warrior/channels.example.json /tmp/channels.json   # 拷到仓外
# 编辑 /tmp/channels.json:把每个 "api_key" 的占位符整串换成真钥匙
# (样例是智谱 open.bigmodel.cn 的两个型号;别的 OpenAI 兼容道同理,
#  改 name/model/base_url 三件套)
```

铁律:**channels.json 永远放仓外**(或进 .gitignore),真钥永不入 git——
样例文件 `channels.example.json` 里有测试钉着,占位符形状不对会红。

## 第四步 · 点火(先空转,再真打;真打=用户批准)

先空转一遍,证明入口是顺的(零模型调用、零写入、零花钱):

```bash
cp -R demos/DEMO-1 /tmp/drydemo    # 拿演示账练手,不碰正主
python3 -m cli.warrior --goal-dir /tmp/drydemo --battle-name DEMO-1 \
  --max-intents 1 --dry-run        # 期望: 打出一大段作战上下文,rc=0
```

真点火长这样(**执行前必须拿到用户明确批准**):

```bash
python3 -m cli.warrior --goal-dir <你的战役目录> --battle-name <战役名> \
  --max-intents 8 --channels /tmp/channels.json --token-cap 500000
```

**预算建议(token-cap 怎么定):**

- 战士默认 `--token-cap` 是 100000——**太小**,别直接用;
- 参照物:DEMO-1(金样 G-r18)整场打下来 `budget.tsv` 记了 **33.5 万 token**
  (4 波:15万/2万/12万/4.5万);
- 所以:**首仗贴实定 500000**(约为参照的 1.5 倍,够打完还有余量);
  宽松上限 2000000(照打不心疼的套餐再用);
- 双保险:环境变量 `TANYIN_BATTLE_BUDGET_CAP_USD` 给战役设美元帽,
  多仗并发时注册表按它仲裁拒新仗;
- 帽子花完战士会停——这不是事故,是设计:宁可半途停,不可失控烧钱。

## 第五步 · 判卷(用结果说话)

```bash
python3 cli/tanyin-ledger verify-chain --goal-dir <战役目录>   # 账没被改坏
python3 scripts/battle.py settle --n 1                          # 收敛结算
```

判卷标准就一条(宪法#43):**真找到了多少能复现的漏洞**。
看三处:`findings.tsv`(发现清单)、`E-index.tsv`(证据卡,每个洞可重放验证)、
`timeline.tsv`(全程审计链)。没有可复现步骤的观察只是 fact,不是 finding。
对照参考:DEMO-1 是 111 发现/709 时间线的形状,你的首仗和它比比看。

---

## 状态清单(本单交付时全部 ✓)

- [x] 靶场能起:`/api/health` ok、登录 200、登录页 200(3081/3082,只听本机)
- [x] 演示战役就位:DEMO-1 验链 PASS(709 行)
- [x] 模型道样例就位:channels.example.json 可被战士真加载、真钥零回流(测试钉)
- [x] 战士入口空转通过:--dry-run rc=0
- [ ] 真点火:等你一句话

**万事俱备,只欠点火。**
