# DEMO-1 · 演示战役(非真战成果)

**这是演示数据,不是真打仗打出来的。** 拷贝自金样夹具 `tests/fixtures/G-r18`
(battle-17 造出的完整战账),用途只有一个:首场真仗前,给「建仗→点火→判卷」
全链一个现成的参照物——你能拿它先跑通验链、看懂账本长相,再开真仗。

## 里面有什么(拷贝自 G-r18,一字未改)

- `findings.tsv`:111 条发现
- `timeline.tsv`:709 行时间线(带哈希链,防篡改)
- 其余 13 表账本文件、证据卡(`findings-cards/`)、证据(`evidence/`)、
  工件(`artifacts/`)等,共 440+ 个文件

## 怎么验收(一分钟)

```bash
python3 cli/tanyin-ledger verify-chain --goal-dir demos/DEMO-1
# 期望输出: PASS verify-chain: 709 行链完整 gate_exit=9 跳门=0
```

## 纪律

- 演示归演示:引用本目录数据时说明「来自演示战役 DEMO-1」,别当成实战胜果报数。
- 想改着玩:拷出去改(`cp -R demos/DEMO-1 /tmp/my-play`),别原地改——
  链会断,`verify-chain` 会 FAIL,那是它该干的活。
- 真仗别在这建:真战目录走 `~/.tanyin/battles/battle-N`(或设 `TANYIN_HOME`),
  首仗五步见 `docs/FIRST-BATTLE-RUNBOOK.md`。
