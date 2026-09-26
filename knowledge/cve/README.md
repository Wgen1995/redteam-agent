# K3 本地 CVE 快照（cve-snapshot.tsv）

- **来源**：NVD / CISA KEV 公共数据精选（公开口径；首批 14 行样例=常见 nday 通路面）。
- **七列格式**：`cve_id` `cpe_prefix` `version_start` `version_end` `severity` `published` `source`
  （severity ∈ {critical, high, medium, low}；source ∈ {NVD, KEV, PSIRT, vendor}；published=ISO 日期）。
- **更新纪律（G-32，批次 6 T9 双通道落定）**：两条**等价**路径任选其一——
  ①命令刷新：`tanyin-install refresh-cve --from <url|file://路径> --home <交战区> --timestamp <ISO8601>`
  （显式人工命令，非定时自动、无常驻进程；下载→sha256 记录→七列 lint 复用校验→原子替换，
  校验不过不落文件；审计行落 `<home>/install-log.tsv`）；②人工重铸：离线整文件重写
  （不做增量补丁）+ 首行 `# snapshot-date:` 注记刷新。种子库快照=冻结资产（R7），
  刷新只落运行时库 `<home>/knowledge/cve/`。
  `lint` 校验七列格式/severity 枚举/published 日期；`nday-match` 输出首行回显快照日期供审计。
- **联网仅核验边界（R11）**：快照匹配纯离线（CPE 前缀+版本区间比较，零 urllib/socket/import 外联）；
  CVE 联网核验=P6 技法页纪律——宿主 WebSearch 对照 PSIRT/NVD/KEV（「明确不信任训练数据」），
  CLI 零外联；页侧 `cve_refs` 须有 `cve_verified` 逐个覆盖（lint 强制），verified_at 距 today 超
  365 天=stale（match 输出 [stale] 降权标注，score 不消费 stale 页）。
- **匹配语义**：命中=cpe 前缀前缀匹配 ∧ version∈[version_start, version_end)
  （`_vtuple` 元组比较：段内取前导数字、非数字段按 0——milestone/里程碑粒度折叠，
  如 10.0.0-M7 与 10.0.0 同元组；区间书写须 end>start，行 7 按此粒度取 10.0.1）。
