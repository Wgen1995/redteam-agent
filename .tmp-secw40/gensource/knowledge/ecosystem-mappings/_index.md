# 生态映射索引（ecosystem-mappings/_index.md）

> 来源：`docs/superpowers/plans/2026-08-08-gensource-security-ontology-catalog.md`（安全本体与行业漏洞全集实现计划）任务3。本文件是生态映射索引。

## 用途

生态映射记录同一统一漏洞语义或本体概念在不同语言/框架中的变体表现——仅API或框架名称不同的内容进入生态变体，不新建UVS。

## 当前索引

| stable_id | name | 适用语言/框架 | version |
|---|---|---|---|
| ECMAP-PYTHON | Python语言生态映射 | Python（CPython运行时） | v0.1 |
| ECMAP-PYTHON-DJANGO | Django框架生态映射 | Python + Django | v0.1 |
| ECMAP-PYTHON-FLASK | Flask框架生态映射 | Python + Flask | v0.1 |
| ECMAP-PYTHON-FASTAPI | FastAPI框架生态映射 | Python + FastAPI | v0.1 |
| ECMAP-JAVA | Java语言生态映射 | Java（JVM运行时） | v0.1 |
| ECMAP-JAVA-SPRING | Spring框架生态映射 | Java + Spring Boot | v0.1 |
| ECMAP-JAVASCRIPT | JavaScript/TypeScript语言生态映射 | JavaScript/TypeScript（Node.js） | v0.1 |
| ECMAP-NODE-EXPRESS | Express框架生态映射 | JavaScript + Express | v0.1 |
| ECMAP-PHP | PHP语言生态映射 | PHP（Zend运行时） | v0.1 |
| ECMAP-PHP-LARAVEL | Laravel框架生态映射 | PHP + Laravel | v0.1 |
| ECMAP-GO | Go语言生态映射 | Go（Golang） | v0.1 |
| ECMAP-CPP | C/C++语言生态映射 | C / C++ | v0.1 |
| ECMAP-RUST | Rust语言生态映射 | Rust | v0.1 |
| ECMAP-CSHARP-DOTNET | C#/.NET生态映射 | C# / .NET / ASP.NET Core | v0.1 |
| ECMAP-RUBY-RAILS | Ruby/Rails生态映射 | Ruby + Ruby on Rails | v0.1 |

## 模板

编写生态映射时参考 [\_template.md](_template.md)（模板不计入正式知识条目，不构成检测能力）。另有旧版模板 `../_templates/ecosystem-mapping-template.md` 保留作沿革参考，新条目使用本目录下的模板。

## 消费方

- `scope-and-context`：范围与威胁语境能力按目标语言/框架过滤适用知识
- `candidate-discovery`：候选发现能力使用生态映射中的识别信号
- `remediation-guidance`：修复指导能力使用生态映射中的框架特定修复写法
