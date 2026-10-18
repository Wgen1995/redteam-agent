# 复审档：哨兵+规划者六件修复 · 2026-10-21

- 评审人：独立代码评审员（只读+跑测+探针，未改任何被评审文件；本档为唯一仓内写）
- 上游：docs/reviews/2026-10-20-review-sentinel-planner.md（一审：哨兵过·规划者打回）
- 修复舰七提交：cbdb91b（哨兵 I-1 换行）/bc08a24（I-1 stderr+兜底）/0ef258d（I-2 持钥）/114b8be（I-4 sweep 线性）/fafa34c+26cf882（I-3 接线+计数）/1811c72（M-5 图单建）
- 修复文件工作树零未提交改动；读到的即 main 提交态。

## 一、修复逐件核（治根判）

**① cbdb91b 哨兵换行（I-1）——治根**。归一落在唯一咽喉 `run_sentinels`（judge_client.py:272 `flat = re.sub(r"\r?\n", " ", corpus)`），全部调用方受益；不是在 write_cmds 拼接点敷面。规则文件零改（判据语义不变）。全角 ４０４ 按一审附注记账不修，并加钉边测试（test_sentinels.py TestNewlineNormalization.test_fullwidth_digits_known_limit_documented）。附带效应：归一后三字段可跨字段命中（题尾+简述头落入同 50 字窗）——确定性、方向偏严（误报闸宁严勿松），全清金样仍绿，接受。

**② bc08a24 stderr 捕获+run 兜底（I-1）——治根**。`_run` 双文件同修合并捕获 stdout+stderr（planner_loop.py:91、replacer.py:206），拒绝原因随文本带回、"dedup_key" 竞速分支复活；测试用 registry lookup 拦截真模拟竞速（对方先落账）断言「合并不 raise」——真走分支非敷面。`run()` 单轮异常兜底（planner_loop.py:208-224）：经 append-timeline 记 `planner-round-fail` 事件（可回放带原因）+清防抖表+静默拍休眠防热循环；`except Exception` 不吞 KeyboardInterrupt，口径正确。

**③ 0ef258d 持钥审批（I-2）——治根**。签名式复用 write_cmds 单源 `_approval_key/_approval_sig`（replacer.py:229 附 --sig），不自铸第二份 HMAC；密钥来源=环境同律（部署面）。环境钥对战士进程可见是一审已记录的既有暴露（docs/reviews/2026-10-15-direction-review/02-security-enforcement.md:27），本修复未加深未引入新面。

**④ 114b8be sweep 线性（I-4）——治根**。头部一趟聚合 `_aggregate`（replacer.py:160）单遍扫 intents/timeline/facts/findings/matrix，classify/续接/收口全程复用同 Session（测试以 Session 计数器钉死 1+N）；trace 计数改词元前缀匹配，对抗性嵌串的收窄在 docstring 诚实声明，且 trace 本就只是审计面非判据（判据=产出+置格，未动）。`_redispatch` 审批行 id 改取 OK 回执行（replacer.py:253）免重读盘，带回退。

**⑤ fafa34c+26cf882 接线（I-3）——治根**。生产者/启动器双补：warrior 收卡 done 终态调 lazy_trigger（cli/warrior/loop.py:253，失败只记 `planner-lazy-fail` timeline 不阻战士，:274-286）；special.py 注册 `planner-loop-start`（启动先记事件入账=首轮必武装+可审计，:217-243）与 `planner-loop-trigger`（单发轮，:254-270）；counts.json 单源派生 55 已同步。闭环两翼齐：常驻有门可入、缺席有收卡惰性补偿。

**⑥ 1811c72 图单建（M-5）——治根**。graph 可选参缺省自建（graph_cmds.py:160，既有调用面行为零变），planner_score 预建传入（planner_score.py:150）；spy 测试钉死只建一遍+可达集结果不变。

## 二、测试面亲跑验真

| 面 | 声称 | 实跑 | 判 |
|---|---|---|---|
| test_sentinel* | 20 | **Ran 20 tests … OK**（0.383s） | 真 |
| test_planner* | 49 | **Ran 49 tests … OK**（2.993s） | 真 |
| tests.test_planner_fixes | 13 | **Ran 14 tests … OK**（14=13+1811c72 的 M-5 一测；计数声称少一，多绿不少绿） | 真 |
| 邻域回归（converge/graph/warrior_loop/phases_yaml + fake_model/v08b_chain） | — | **40+13 全 OK** | 无回归 |

修复测试非空壳实证：竞速测试真拦截 registry.lookup 让对方先落账再断言合并（test_planner_fixes.py:98-130）；持钥测试用 `_row_sig_ok` 复算验签（:210-236）；万格基准直接构 30k+20k 表（:247-286）；收卡触接战具=假模型服务+记录型 spawn 不触网（:355-415）。

## 三、四组新探针（独立复测，临时目录+零端口）

1. **换行+全角组合**：LF/CRLF/三连换行/换行混半角 404/SEN-011 多行——全部命中（LF→downgrade-to-fact、CRLF→downgrade-to-fact、多行低置信→**reject**）；纯全角 ４０４→clear（记账极限，与其钉边测一致）。**端到端复测原 I-1 攻击**：title 带裸 \n 的同款 404 误报 → `OK\tF-g1-0003\tfacts.tsv`（降级走 facts，不再入 findings）。判：闭合。
2. **持钥+幂等二扫**：TANYIN_APPROVAL_KEY 在场，一扫=断线卡 fault-redispatch 重入 active、审批恰 1 行且持钥方可复算验签（`_row_sig_ok`=True）；二扫=零重复动作零崩溃；三扫（新故障卡）=新审批恰 1 行。判：闭合。
3. **万格 0.41s 复测**：按一审原口径（intents=10k/timeline=30k/facts=20k/matrix=10k）真跑 RP.sweep 两次：**0.311s/0.314s**（一审旧路径同规模纯扫描 8.32s，≈27×；Session 全量读盘单独 0.265s=聚合趟只加 ~0.05s，确系线性）；聚合口径逐项精确（trace=30000/outputs=20000/marks=10000，行数 10000）。舰报 0.41s 与本机复测同量级。判：闭合。
4. **收卡触发恰一次**：假模型战具独立复跑——done 收卡：触发恰 1 次、goal_dir 正确、时间戳非空；blocked（max-turns 不收敛）收卡：触发 0 次、无 lazy-fail 留痕；代码面单调用点在 done 分支即返（cli/warrior/loop.py:253-254）。判：闭合。

## 四、遗留与记账（均为 Minor，不阻收舱）

- 一审 Minor 未修且仍开（与修复舰声称范围一致，账面无漂移）：哨兵 M-1 命中零留痕+注释不实（write_cmds.py:787）、M-2 逐 finding 重载规则库、M-3 未来规则 ReDoS 护栏+corpus 无截断、M-4 K6 pattern 取标题、M-5 降级丢 --supersede/重复降级 fact；规划者 M-1 轮后基线吞并发写（planner_loop.py:187）、M-2 伪造 transport-fault reason（有界）、M-3 budget_share=1;1;1 绝对值（planner_loop.py:125）、M-4 historical_yield 把证伪/被合并行计收益（planner_score.py:202-212）。
- 复审新增两条记账：① 惰性触发只挂 done 终态——blocked/rejected 收卡后若再无 done、无常驻、无手动 trigger，则该批终态不被扫面（sweep 全局，任一触发即清；设计允许，建议后续把 blocked 终态也挂同触发或缩短口径差）；② 换行归一后跨字段命中面略宽（见①附注，方向安全）。

## 五、结论

- 哨兵 5e9c318（含修复 cbdb91b）：**过——正式收舱**。
- 规划者 b3beebf（含修复 bc08a24/0ef258d/114b8be/fafa34c/26cf882/1811c72）：**过——正式收舱**。
- 六件 Important/M-5 全部治根、证据在档；遗留全为 Minor 记账，无新增 Important/Critical。

## 六、复验指令

```
cd /Users/wgen/redteam-agent
python3 -m unittest discover -s tests -p "test_sentinel*"    # 20/20
python3 -m unittest discover -s tests -p "test_planner*"     # 49/49
python3 -m unittest tests.test_planner_fixes -v              # 14/14
```
四组探针脚本为临时目录纯函数/CLI 级复测（假模型服务绑 127.0.0.1:0 动态口，不触 8900 等固定端口）；本评审唯一仓内写=本档。
