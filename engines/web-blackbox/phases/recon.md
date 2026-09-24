# 段① 侦察测绘（recon）——加载：intent.kind = recon

单写者铁律：你只产 submissions/<intent-id>/submission.json；一切落账由总控验收后执行。
界内界外都记（界外自动标 out_of_scope，账本级禁止派生 intent——总控职责）。

## A1-A8×通道×落账引擎位表（资产宇宙完备性口径）

| 资产类 | 通道（每类≥3 正交） | 落账（提交侧填 assets[]/facts[]，总控执行） |
|---|---|---|
| A1 标识层 | 被动证书透明日志/主动 DNS 字典/内容挖掘 SPF-CNAME | add-asset --type=root-domain/subdomain＋add-fact kind=info |
| A2 网络层 | 主动端口扫描/被动历史库/内容挖掘响应头 | add-asset --type=ip＋add-fact kind=port |
| A3 服务层 | 主动指纹/被动 banner/历史服务快照 | add-asset --type=service＋add-fact kind=service |
| A4 应用层 | 内容挖掘前端入口/主动路径探测/外推同构部署 | add-asset --type=app/endpoint＋add-fact kind=http |
| A5 存储与云 | 对象桶枚举/数据库暴露探测/云元数据端点/CDN 源站/队列 | add-asset --type=cloud-storage（meta=sub:object-bucket 等）＋add-fact kind=info |
| A6 代码与物料 | 前端源码挖掘/JS sourcemap/历史泄露快照 | add-asset --type=source-code＋add-fact kind=info |
| A7 人的因素 | 邮箱规格猜测/账号名枚举/泄露库命中（只查不撞库）/SSO 依赖 | add-asset --type=human-factor（meta=sub:email 等）＋add-fact kind=info |
| A8 关联外推 | 母公司域关联/同证书 SAN 外推/命名规律外推 | add-asset（meta=extrapolated）＋add-fact kind=vuln-clue |

## 完备性口径（图谱驱动增补 71d3b7c）
侦察分母=graph-horizon 可达集（总控跑 tanyin-ledger graph-horizon --from=<立足点>）：
可达资产上仍有未测空格=侦察未完备，优先补该资产正交通道；外推发现先 scope 复判再入图。
诱饵（客户配合植入界内）命中只记不炫耀：facts[] kind=info＋note=canary。

## 提交纪律
发现新资产→assets[]（type/value/meta）；观察→facts[]（kind/target/detail 脱敏/confidence）；
不铸 ID（总控 next-id）；不写矩阵。预算内做不完→status=partial 附已完成清单。
