# GT 考卷就位检查（ZhuLong 首仗判卷真相）· 2026-10-20

> 结论先行：**仓外 `~/.tanyin/gt/` 没有可用的 ZhuLong-3081 代卷**——现有 16 份全是 docker 靶场卷的拷贝；ZhuLong 代卷须点火前从靶场事实清单产一卷（步骤见§三），否则 `battle.py settle` 判分用错卷。

## 一、现状盘点（2026-10-20 实测）

| 位置 | 内容 | 可用性 |
|---|---|---|
| `~/.tanyin/gt/` | G-r28.json .. G-r43.json 共 16 份 | ❌ 全是 `battle.py init` 的 ensure_gt 拷贝（battle.py:27,38-40），键=svc-* docker 靶场端点（range-56-v5 系）——**对 ZhuLong-3081 无效** |
| 仓内 `tests/range/ground-truth.json` | range-56-v5（56 面，keying v7） | ❌ docker 靶场卷；且它是 init 的拷贝源——新战 init 会自动把它拷到 `~/.tanyin/gt/<gen>.json`（**错卷自动进位**，须覆盖，见§三步5） |
| 仓内 `evals/gt/battlefields/zl-*.json` | zl-webface-v1（4 open+2 回归锚+3 诱饵）/zl-supplychain-v1（2 open+2 锚+2 诱饵）/zl-chain-v1（2 链 7 环） | ✅ **这就是靶场事实清单本体**（source-gt 白盒源码锚，ARTEX 实测+Z:206-208 互证）；gt_verify 实测 27/27 pass——但它是源码锚口径，不是 3081 黑盒会话判分卷 |

## 二、事实清单 → 代卷分母（哪些行能进 3081 黑盒卷）

| GT 行 | 类 | 3081 黑盒可达性 | 进卷建议 |
|---|---|---|---|
| zl-web-01 探活 SSRF（POST /api/environments/:id/health） | ssrf | ✅ API 面直打（需登录态+至少一个 environment） | 进 |
| zl-web-02 imports sourceDir 任意目录读 | arbitrary-file-read | ✅ API 面直打（POST /api/imports） | 进 |
| zl-web-03 会话面零 Origin/Referer 校验 | csrf | ✅ 写面全站可验 | 进 |
| zl-web-04 项目名零约束反射 | xss | ✅ 建项目即验 | 进 |
| zl-sup-01 runner 注册/令牌零授权绑定 | broken-access-control | ⚠️ 须 runner/provision 面活（数据面是否就绪点火前验） | 条件进 |
| zl-sup-02 runner-auth 信息泄 | infoleak | ⚠️ 同上 | 条件进 |
| zl-web-05/06、zl-sup-03/04（fixed-anchor） | 回归锚 | — | 不进黑盒卷（源码锚语义，留 gt_verify 面） |
| zl-*-d0*（neg 诱饵 5 行） | decoy | — | **照搬进卷**（FP 口径=报告 neg 行即误报） |
| zl-chain-v1（2 链） | chain | 链级判分走 gt_eval --chain（range 链）；源码链走 gt_verify | 不进 session 卷，单列 |

## 三、产卷步骤（从事实清单产一卷，约一手工活）

1. **定 gen 名**：CLI 建战用 `--gen`（如 `G-zl1`）或 webui 建（gen=G-w1，server.py:120）；代卷文件名=<gen>.json。
2. **逐行转 session-gt 形**（同 `tests/range/ground-truth.json` 形状，scorer 单源吃这个）：
   ```json
   {"format_version": 1,
    "note": "ZhuLong-3081 黑盒代卷 v1——源自 evals/gt zl-webface/zl-supplychain open 行",
    "host_aliases": {"127.0.0.1:3081": ["localhost:3081"]},
    "planted": [
      {"id": "zl-web-01", "class": "ssrf", "endpoint": "127.0.0.1:3081/api/environments/<n>/health", "marker": "<活体特异串>", "post_auth": true, "authz_role": "user"}
    ]}
   ```
   - 键口径：host+path 形、query 剥离、尾段数字归一（keying v7 全套在 scorer；RUNBOOK「GT 键口径」节=tests/range/RUNBOOK.md 首屏后第一节，开打前必读）。
3. **marker=活体响应特异串**：ZhuLong 是真实产品非种子靶场，**无 planted 信标**——marker 取该洞响应里可区分的稳定串（点火前实勘敲定，一洞一串，写进 note 备查）。这是与 docker 卷的唯一口径差，判分报告须标注「活体 marker 口径」。
4. **负对照搬**：zl-web-d01..d03 + zl-sup-d01..d02 五行照搬（id/class 保持，endpoint 换 3081 形）。
5. **覆盖错卷**：`battle.py init` 之后（ensure_gt 已把 docker 卷拷到位），用本卷**覆盖** `~/.tanyin/gt/<gen>.json`——settle 只读仓外位（battle.py:50-53 settle_gt 优先仓外）。
6. **判分**：
   ```bash
   python3 tests/eval_range_recall.py --session ~/.tanyin/battles/battle-<N>/<gen> --ground-truth ~/.tanyin/gt/<gen>.json
   ```
7. **链式面**（可选）：`python3 evals/gt/gt_eval.py --session <goal-dir> --chain evals/gt/battlefields/zl-chain-v1.json`——源码链本件走 `gt_verify.py --live`（对 ZhuLong 仓只读实跑）。

## 四、就位判据（点火前打勾）

- [ ] `~/.tanyin/gt/<gen>.json` 存在且 `python3 -c "import json;json.load(open(...))"` 过
- [ ] planted 行数=§二「进」+「条件进」实勘后的行数；neg 5 行在
- [ ] 每行 marker 已点火前实勘（活体响应串钉死）
- [ ] host_aliases 声明 3081 两形
- [ ] **未就位而点火**的降级预案：settle 前补卷重跑判分；判分报告记「卷后补，首考纪律不受影响（立基线不比旧）」
