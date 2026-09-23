# 探隐 deny-list（版本化数据文件）

来源：设计定稿 §8.3——命令执行前置机械比对模式清单（LLM 自标注错误时的最后防线）。
消费方：cli/ledger/enforce.py（Tier1 tanyin-guard / Tier2 hooks/simulate.py 同源）。
匹配语义：参数连接串子串命中即拒（大小写敏感）；「format 」含尾随空格防误伤 information。
同步纪律：本文件与 enforce.DENY_EMBEDDED 为同份拷贝（缺文件/空文件时内嵌兜底），
两处必须同步改——tests/test_enforce_unit.py::DenyListData 钉死一致。

version: 1

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
