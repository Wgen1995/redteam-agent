# ECMAP-GO：Go语言生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-GO |
| name | Go语言生态映射 |
| version | v0.1 |
| 适用语言/框架 | Go（Golang，不含Web框架——net/http为标准库） |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `go.mod` / `go.sum` | Go模块依赖文件 |
| 文件标记 | `.go`源文件 + `package`声明 | Go源码标识 |
| 文件标记 | `main.go` / `cmd/`目录 | Go入口文件/目录 |
| 框架标记 | `import "net/http"` | 标准库HTTP |
| 框架标记 | `gin` / `echo` / `chi` / `fiber` in `go.mod` | 第三方Web框架 |
| 运行时标记 | `go build` / `go run` | Go构建/运行 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| HTTP Handler | `http.HandleFunc("/path", handler)` | 标准库路由 |
| ServeMux | `mux := http.NewServeMux(); mux.Handle("/path", h)` | 多路复用器 |
| 框架路由 | `r.GET("/path", handler)` (Gin) / `e.GET("/path", handler)` (Echo) | 框架路由 |
| main函数 | `func main() { ... }` | Go程序入口 |
| gRPC | `pb.RegisterXServiceServer(s, &server{})` | gRPC服务注册 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| HTTP中间件 | `func mw(next http.Handler) http.Handler { ... }` | 中间件包装函数 |
| 框架中间件 | `r.Use(middleware)` (Gin) / `e.Use(mw)` (Echo) | 框架中间件注册 |
| recover | `func recover mw` | panic恢复中间件 |
| logging | 请求日志中间件 | 审计日志 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 查询参数 | `r.URL.Query().Get("param")` | 攻击者可控 |
| 路径参数 | `chi.URLParam(r, "id")` / `c.Param("id")` (Gin) | 攻击者可控 |
| 请求体 | `json.NewDecoder(r.Body).Decode(&data)` / `io.ReadAll(r.Body)` | 攻击者可控 |
| 请求头 | `r.Header.Get("X-...")` | 攻击者可控 |
| Cookie | `r.Cookie("name")` | 攻击者可控 |
| 表单 | `r.ParseForm(); r.Form.Get("param")` / `r.PostForm.Get("param")` | 攻击者可控 |
| 环境变量 | `os.Getenv("VAR")` | 部分可控 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| SQL执行 | `db.Query(sql)` / `db.Exec(sql)` / `db.QueryContext(ctx, sql)` | 注入风险（拼接时） |
| 命令执行 | `exec.Command(name, args...)` | 命令注入风险（参数拼接时） |
| 文件操作 | `os.Open(path)` / `os.ReadFile(path)` / `filepath.Join(dir, name)` | 路径遍历风险 |
| 模板渲染 | `template.Execute(w, data)` / `html/template` | html/template自动转义 |
| 代码执行 | 无原生eval（Go是编译语言） | N/A |
| 反序列化 | `gob.Decode()` / `json.Unmarshal()` | gob反序列化风险 |
| 网络请求 | `http.Get(url)` / `http.Post(url, ...)` / `http.Client.Do(req)` | SSRF风险 |
| 重定向 | `http.Redirect(w, r, url, 301)` | 开放重定向风险 |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| 中间件鉴权 | `func authMW(next http.Handler) http.Handler { ... }` | 自定义鉴权中间件 |
| JWT | `github.com/golang-jwt/jwt` | JWT库 |
| Casbin | `github.com/casbin/casbin` | 访问控制框架 |
| Session | `github.com/gorilla/sessions` | 会话管理 |
| 基本认证 | `r.SetBasicAuth(user, pass)` | HTTP Basic认证 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 输入校验 | `go-playground/validator` / 手动检查 | 结构体验证 |
| SQL参数化 | `db.Query("SELECT ... WHERE col = $1", value)` / `db.QueryContext(ctx, sql, args...)` | 参数化查询 |
| HTML净化 | `html/template`自动转义 | html/template包 |
| 路径净化 | `filepath.Clean()` / `filepath.Abs()` + `strings.HasPrefix()` | 路径规范化 |
| 命令参数 | `exec.Command(name, args...)` 参数数组形式 | 参数数组替代shell |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | `html/template` `{{.Value}}` 自动转义 | html/template自动HTML转义 |
| HTML属性 | `html/template` 自动转义 | 自动处理 |
| JavaScript | `html/template` `{{.Value}}` 在JS上下文 | 上下文感知转义 |
| URL | `url.QueryEscape()` / `template.URLQueryEscaper` | URL编码 |
| text/template | `text/template` `{{.Value}}` | **不转义**——text/template不自动转义 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| database/sql | `db.Query("SELECT ... WHERE col = $1", value)` | 参数化——`$1`/`?`占位符 |
| database/sql + sqlx | `db.Select(&dest, "SELECT ... WHERE col = $1", value)` | 参数化 |
| GORM | `db.Where("col = ?", value).Find(&results)` | 需用`?`占位符 |
| GORM Raw | `db.Raw("SELECT ... WHERE col = ?", value).Scan(&result)` | 需参数化 |
| GORM危险 | `db.Where(fmt.Sprintf("col = '%s'", value))` | **危险**——Sprintf拼接 |
| ent | `client.User.Query().Where(user.NameEQ(value))` | 参数化默认开启 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON | `json.Marshal()` / `json.Unmarshal()` | 安全 |
| gob | `gob.NewDecoder().Decode()` | gob反序列化——注意类型安全 |
| XML | `encoding/xml` / `xml.NewDecoder()` | XXE风险——Go默认不处理外部实体（较安全） |
| YAML | `gopkg.in/yaml.v3` | YAML解析——v3比v2更安全 |
| CSV | `encoding/csv` | CSV公式注入风险 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| goroutine | `go func() { ... }()` | 轻量级线程——需注意共享状态 |
| channel | `ch := make(chan T)` / `<-ch` / `ch <- val` | 通道通信 |
| sync.Mutex | `mu.Lock(); defer mu.Unlock()` | 互斥锁——defer确保释放 |
| sync.RWMutex | `mu.RLock(); defer mu.RUnlock()` | 读写锁 |
| sync.WaitGroup | `wg.Add(1); wg.Done(); wg.Wait()` | 等待组 |
| context | `context.WithCancel()` / `context.WithTimeout()` | 上下文取消 |
| atomic | `atomic.AddInt64()` / `atomic.Value` | 原子操作 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 反射 | `reflect.TypeOf()` / `reflect.ValueOf()` | 运行时类型检查 |
| 接口 | `interface{}` / `any` | 动态类型——需类型断言 |
| 代码生成 | `go generate` / `stringer` | 编译时代码生成 |
| Wire DI | `github.com/google/wire` | 编译时依赖注入 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 构建 | `go build` / `go install` | 编译为单一二进制 |
| 包管理 | `go mod` / `go get` | Go模块系统 |
| 测试框架 | `testing` / `testify` | Go内置测试 |
| 静态分析 | `go vet` / `staticcheck` / `gosec` | gosec安全专项 |
| 依赖扫描 | `govulncheck` | 官方漏洞扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| html/template转义 | 开启 | `html/template`自动上下文感知转义 |
| text/template转义 | 不转义 | `text/template`不转义——Web输出应用html/template |
| SQL参数化 | 需手动 | `db.Query`需手动用占位符 |
| TLS | 需配置 | `http.ListenAndServeTLS`需手动配置 |
| 内存安全 | 安全 | Go提供内存安全（无缓冲区溢出） |
| 并发安全 | 需注意 | goroutine共享状态需同步 |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Go 1.22+ | `net/http`路由模式增强 | 路径参数原生支持 |
| Go 1.21+ | `slices` / `maps`标准库 | 更安全的数据操作 |
| Go 1.20+ | `errors.Join` | 错误处理改进 |
| Go 1.18+ | 泛型支持 | 类型安全增强 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——fmt.Sprintf拼接SQL |
| vuln-patterns | VULN-INJ-CMD-01 | 命令注入——exec.Command参数拼接 |
| vuln-patterns | VULN-INJ-SSRF-01 | SSRF——http.Get可控URL |
| vuln-patterns | VULN-FILE-TRAVERSAL-01 | 路径遍历——os.Open+filepath.Join |
| vuln-patterns | VULN-FILE-SEARCHPATH-01 | 不可信搜索路径——exec无绝对路径 |
| vuln-patterns | VULN-ENC-ENCODING-01 | 输出编码失效——text/template |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权缺失——无鉴权中间件 |
| vuln-patterns | VULN-CONC-RACE-01 | 竞态条件——goroutine共享状态无锁 |
| vuln-patterns | VULN-CONC-LOCKING-01 | 锁使用不当——无defer Unlock |
| vuln-patterns | VULN-EXC-UNCHECKED-01 | 返回值未检查——error被_忽略 |
| vuln-patterns | VULN-CALC-INTOVERFLOW-01 | 整数溢出——malloc(len*sizeof)无检查 |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——http.Redirect可控URL |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 信息泄露——错误信息含内部路径 |
| attack-patterns | ATK-INJ-CMD-01 | 良性命令注入标记证明 |
| attack-patterns | ATK-INJ-SSRF-01 | 良性SSRF回调探测 |
| attack-patterns | ATK-FILE-TRAVERSAL-01 | 良性路径遍历读取证明 |
| attack-patterns | ATK-CONC-RACE-01 | 竞态条件良性证明 |
| attack-patterns | ATK-CONC-LOCKING-01 | 死锁良性证明 |
| attack-patterns | ATK-EXC-UNCHECKED-01 | 未检查错误路径良性证明 |
| attack-patterns | ATK-CALC-INTOVERFLOW-01 | 整数溢出良性证明 |
| fix-patterns | FIX-SQLI-PARAMQUERY-01 | db.Query参数化 |
| fix-patterns | FIX-INJ-CMD-01 | exec.Command参数数组 |
| fix-patterns | FIX-FILE-TRAVERSAL-01 | filepath.Clean+Abs+前缀检查 |
| fix-patterns | FIX-CONC-LOCKING-01 | defer Unlock |
| fix-patterns | FIX-EXC-UNCHECKED-01 | error检查替代_ |
| fix-patterns | FIX-CALC-INTOVERFLOW-01 | 整数溢出检查 |

## 正例/负例

**正例**（Go中的安全写法）：
```go
// SQL参数化
rows, err := db.Query("SELECT * FROM users WHERE id = $1", userId)
if err != nil { /* handle error */ }
defer rows.Close()

// 命令执行用参数数组
cmd := exec.Command("ls", "-la", userDir)
output, err := cmd.Output()

// html/template自动转义
tmpl := template.Must(template.New("page").Parse(`<div>{{.Name}}</div>`))
tmpl.Execute(w, data)

// 路径遍历防护
cleanPath := filepath.Clean(filepath.Join(baseDir, filename))
absPath, err := filepath.Abs(cleanPath)
if err != nil || !strings.HasPrefix(absPath, baseDirAbs) {
    http.Error(w, "Invalid path", http.StatusForbidden)
    return
}

// 锁+defer释放
var mu sync.Mutex
mu.Lock()
defer mu.Unlock()
// critical section
```

**负例**（Go中的不安全写法）：
```go
// SQL拼接
rows, err := db.Query(fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", name))

// text/template不转义
tmpl := template.Must(template.New("page").Parse(`<div>{{.Name}}</div>`))  // text/template
tmpl.Execute(w, data)

// 错误忽略
val, _ := strconv.Atoi(input)  // error被_忽略

// 锁无defer
mu.Lock()
doSomething()  // 如果panic，锁不释放
mu.Unlock()

// 命令注入
cmd := exec.Command("sh", "-c", "ls " + userDir)

// 重定向无验证
http.Redirect(w, r, r.URL.Query().Get("redirect"), http.StatusFound)
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Go技术栈
- candidate-discovery：使用Go Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用Go安全API/Encoder映射提供修复写法

## 官方来源

- 官方文档：https://go.dev/doc/
- 安全指南：https://go.dev/security/
- gosec：https://github.com/securego/gosec
- govulncheck：https://go.dev/blog/vuln

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Go语言生态映射 |
