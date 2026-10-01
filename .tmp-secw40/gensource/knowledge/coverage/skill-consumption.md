# Skill消费索引（coverage/skill-consumption.md）

> 本文件记录每类知识被哪个Skill消费、加载条件和未匹配时的表达，供知识接线验证和覆盖追踪。

## 消费索引格式

| 字段 | 说明 |
|---|---|
| 知识库 | 知识库目录名（vuln-patterns/attack-patterns/fix-patterns/ecosystem-mappings） |
| 消费Skill | 消费该知识库的GenSource能力名称 |
| 加载条件 | 何时消费（按输入表/执行步骤/输出字段定位） |
| 消费字段 | Skill从知识条目中读取的具体字段 |
| 匹配时输出 | 命中时Skill输出的引用字段 |
| 未匹配时表达 | 未命中时Skill必须的显式表达 |
| 知识缺口处理 | 未匹配时是否进入知识演进 |

## 消费索引

### vuln-patterns

| 消费Skill | 加载条件 | 消费字段 | 匹配时输出 | 未匹配时表达 | 知识缺口处理 |
|---|---|---|---|---|---|
| candidate-discovery | 执行步骤A.2（模式驱动发现） | 触发信号、适用语言/框架、Source/Propagation/Sanitizer/Sink、可执行发现步骤、排除条件 | `vuln_pattern_refs`、`knowledge_consultations[]`中的`consultation_result=matched_pattern`项 | `knowledge_consultations[]`存在`consultation_result=not_matched`项，显式写"未匹配，可能是新模式" | 写`capability_gap_refs`进入#16 |
| verification-and-rating | 执行步骤A.3（候选专属校验清单） | 验证方法、反证方法、排除条件、Observable Oracle | 候选专属校验清单items引用vuln-pattern排除条件 | 标注"该候选尚无对应vuln-pattern验证方法，按#4独立判断" | 写`capability_gap_refs` |
| remediation-guidance | 通过fix-patterns反向引用间接消费 | 修复模式引用 | 通过fix-pattern_ref间接引用 | 由fix-patterns未匹配表达覆盖 | 由fix-patterns缺口处理覆盖 |

### attack-patterns

| 消费Skill | 加载条件 | 消费字段 | 匹配时输出 | 未匹配时表达 | 知识缺口处理 |
|---|---|---|---|---|---|
| exploit-proof | 输入表（knowledge/attack-patterns/）+ 执行步骤A/B | 适用条件、前置权限、输入载体、最小危害证明目标、Observable Oracle、Executed/Inferred证明步骤、隔离要求、禁止行为 | `attack_pattern_refs`、匹配状态 | 允许临时安全证明，但记录"未匹配attack-pattern，本次采用临时实现"并进入知识演进 | 写`capability_gap_refs`进入#16 |
| verification-and-rating | 执行步骤A.3（候选专属校验清单）参考 | 控制绕过检查、Observable Oracle | 候选专属校验清单参考attack-pattern的控制绕过检查 | 标注"无对应attack-pattern，按#4独立判断控制绕过" | 写`capability_gap_refs` |

### fix-patterns

| 消费Skill | 加载条件 | 消费字段 | 匹配时输出 | 未匹配时表达 | 知识缺口处理 |
|---|---|---|---|---|---|
| remediation-guidance | 执行步骤B1（窄范围战术修复） | 需要恢复的安全不变量、首选控制/替代控制、禁止的表面修补、安全API、版本兼容性、数据迁移、安全负向测试、合法行为正向测试、根因组复查、兄弟实例复查、等价Sink与绕过检查、回滚、修复后监测 | `fix_pattern_ref` | 显式写"未匹配，本次修复为个案定制，未套用标准fix-pattern" | 由#7按个案定制处理，记录知识缺口 |
| remediation-guidance（独立对抗复核） | 执行步骤D | 等价Sink与绕过检查 | `bypass_review_result`引用fix-pattern绕过检查 | 标注"无对应fix-pattern绕过检查，按独立对抗复核独立判断" | 由#7独立对抗复核处理 |

### ecosystem-mappings

| 消费Skill | 加载条件 | 消费字段 | 匹配时输出 | 未匹配时表达 | 知识缺口处理 |
|---|---|---|---|---|---|
| scope-and-context | 执行步骤A.1（技术栈探测）+ B.2（按本体链路消费权威索引） | 识别信号、入口注册、中间件/过滤器/拦截器 | `ecosystem_mapping_refs`（写入generation_basis或攻击面地图） | 标注"该语言/框架无对应生态映射，完整性置信度较低" | 写`knowledge_gaps`进入开放语义复查 |
| candidate-discovery | 执行步骤A.2（按生态过滤vuln-patterns） | Source API、Sink API、Guard与授权框架 | 按生态过滤适用vuln-pattern条目 | 标注"该生态无映射，按通用触发信号匹配" | 写`capability_gap_refs` |
| remediation-guidance | 执行步骤B1（按语义匹配fix-patterns） | 安全API、Encoder与输出上下文、ORM与Raw API | 按生态匹配框架特定修复写法 | 标注"该生态无映射，按通用安全API处理" | 由#7个案定制 |

## 覆盖状态

| 知识库 | 条目数 | 消费Skill数 | 接线状态 |
|---|---|---|---|
| vuln-patterns | 6 | 3 | 已接线（candidate-discovery/verification-and-rating/remediation-guidance） |
| attack-patterns | 4 | 2 | 已接线（exploit-proof/verification-and-rating） |
| fix-patterns | 6 | 1 | 已接线（remediation-guidance） |
| ecosystem-mappings | 0条目+1模板 | 3 | 模板就绪，待条目填充 |
