# 探隐 deny-list（版本化数据文件）

来源：设计定稿 §8.3——命令执行前置机械比对模式清单（LLM 自标注错误时的最后防线）。
消费方：cli/ledger/enforce.py（Tier1 tanyin-guard / Tier2 hooks/simulate.py 同源）。
匹配语义：参数连接串子串命中即拒（大小写敏感）；「format 」含尾随空格防误伤 information。
同步纪律：本文件与 enforce.DENY_EMBEDDED 为同份拷贝（缺文件/空文件时内嵌兜底），
两处必须同步改——tests/test_enforce_unit.py::DenyListData 钉死一致。

version: 2

## 模式清单

- rm -rf /
- rm -rf ./
- rm -rf .
- rm -fr /
- rm -fr ./
- rm -fr .
- rm -rf ~
- rm -fr ~
- drop database
- truncate table
- :(){:|:&};:
- :(){ :|:& };:
- mkfs
- dd if=
- dd of=/dev/
- shutdown
- reboot
- halt
- init 0
- init 6
- format 
- > /dev/sd
- > /dev/vd
- chmod -R 777 /

## v2 增补（OP1，2026-10-14：02-opsec 缺口3）

打穿别打塌：v1 24 模式全是毁灭单命令，无 DoS 工具/激进档/BENCHMARK 型。v2 以
**调用形态锚定**补齐——DoS 专用工具取脚本名.扩展名/-d 旗标形，文档字样
（cat hulk-notes.md / grep hulk）不含调用形不误伤；激进档/BENCHMARK 型取
nmap -T5（insane 档）/ sqlmap risk·level 满档 / ab·hey·wrk·siege 并发压测
旗标形。nuclei 的 dos/intrusive 排除另由调用模板固化（-rl 50 -etags
dos,intrusive）+ guard 执行通道机械执法，不走本清单。

- slowloris.py
- slowloris.pl
- hulk.py
- goldeneye.py
- torshammer.py
- slowhttptest -d
- -T5
- --risk=3
- --level=5
- ab -n
- hey -z
- siege -c
- wrk -t
