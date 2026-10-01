# ECMAP-RUST：Rust语言生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-RUST |
| name | Rust语言生态映射 |
| version | v0.1 |
| 适用语言/框架 | Rust（无GC，所有权系统内存安全，unsafe可绕过） |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `Cargo.toml` / `Cargo.lock` | Rust项目依赖文件 |
| 文件标记 | `.rs`源文件 | Rust源码标识 |
| 文件标记 | `src/main.rs` / `src/lib.rs` | Rust入口文件 |
| 框架标记 | `use std::net::TcpListener` / `use actix_web` / `use axum` | Web框架/网络库 |
| 运行时标记 | `target/` 目录 | Cargo构建产物 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| main函数 | `fn main() { ... }` | Rust程序入口 |
| HTTP Handler | `async fn handler(req: Request) -> Response` | Web框架Handler |
| actix路由 | `App::new().route("/path", web::get().to(handler))` | actix-web路由 |
| axum路由 | `Router::new().route("/path", get(handler))` | axum路由 |
| 命令行 | `clap::Parser` / `std::env::args()` | CLI入口 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| Tower中间件 | `tower::ServiceBuilder` / `tower-http` | Tower中间件生态 |
| actix中间件 | `wrap(middleware)` | actix-web中间件 |
| axum中间件 | `Router::new().layer(middleware)` | axum中间件层 |
| 错误处理 | `Result<T, E>` / `?` 操作符 | Rust错误处理模式 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 查询参数 | `req.query_string()` / 框架提取 | 攻击者可控 |
| 路径参数 | `Path(id): Path<i32>` (axum) | 攻击者可控 |
| 请求体 | `Json(data): Json<Payload>` (axum) | 攻击者可控（经serde验证） |
| 请求头 | `req.headers().get("x-...")` | 攻击者可控 |
| 环境变量 | `std::env::var("VAR")` | 部分可控 |
| 命令行 | `std::env::args()` / `clap` | 取决于调用方 |
| 文件输入 | `std::fs::read()` / `std::io::Read` | 攻击者可控（文件内容） |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| SQL执行 | `sqlx::query(sql)` / `diesel::query` | 注入风险（拼接时） |
| 命令执行 | `std::process::Command::new(name).args(args)` | 命令注入风险（参数拼接时） |
| 文件操作 | `std::fs::File::open(path)` / `std::path::PathBuf` | 路径遍历风险 |
| unsafe块 | `unsafe { ... }` | 绕过安全检查——UAF/溢出风险 |
| FFI | `extern "C" { ... }` | 外部函数接口——绕过安全保证 |
| 模板渲染 | `askama` / `tera` / `handlebars` | XSS风险（需autoescape） |
| 网络 | `reqwest::get(url)` / `hyper` | SSRF风险 |
| 反序列化 | `serde_json::from_str()` / `bincode::deserialize()` | 安全（serde无代码执行） |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| 中间件鉴权 | Tower中间件 / actix extractor | 自定义鉴权中间件 |
| JWT | `jsonwebtoken` crate | JWT验证 |
| Session | `tower-sessions` / `actix-session` | 会话管理 |
| 权限 | `casbin-rs` | 访问控制 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 输入校验 | `serde` + `validator` crate | 结构化反序列化+验证 |
| SQL参数化 | `sqlx::query("SELECT ... WHERE col = $1").bind(value)` | 参数化查询 |
| HTML净化 | ` ammonia` crate | HTML净化 |
| 路径净化 | `std::fs::canonicalize()` + `starts_with()` | 规范化+前缀验证 |
| 命令参数 | `Command::new(name).args(args)` 参数数组 | 参数数组（无shell） |
| 模板转义 | `askama` / `tera` autoescape | 默认HTML转义 |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | `askama` `{{ value }}` 自动转义 | 默认HTML转义 |
| HTML属性 | `askama` 自动转义 | 自动处理 |
| JavaScript | `askama` `{{ value|json }}` | JSON编码 |
| URL | `urlencoding::encode()` | URL编码 |
| 不转义 | `askama` `{{{ value }}}` 或 `|safe` | **危险**——不转义输出 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| sqlx | `sqlx::query_as("SELECT ... WHERE col = $1").bind(value)` | 参数化——`$1`占位符 |
| diesel | `users::table.filter(users::name.eq(name)).load(&conn)` | 编译时类型安全 |
| sea-orm | `entity::find_by_id(id).one(db).await` | 参数化默认 |
| Raw SQL | `sqlx::query(format!("SELECT ... WHERE col = '{}'", value))` | **危险**——format!拼接 |
| rusqlite | `conn.prepare("SELECT ... WHERE col = ?1")?.query(rusqlite::params![value])` | 参数化 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| serde JSON | `serde_json::from_str()` / `serde_json::to_string()` | 安全 |
| bincode | `bincode::deserialize()` | 二进制序列化——安全 |
| XML | `quick-xml` / `serde-xml-rs` | XXE风险——需注意解析器配置 |
| TOML | `toml::from_str()` | 安全 |
| unsafe transmute | `std::mem::transmute()` | **极危险**——绕过类型系统 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| async/await | `async fn` / `.await` | Tokio/async-std运行时 |
| tokio | `tokio::spawn(async {})` | 异步任务 |
| 线程 | `std::thread::spawn()` | OS线程 |
| Mutex | `std::sync::Mutex` / `tokio::sync::Mutex` | 互斥锁——RAII自动释放 |
| RwLock | `std::sync::RwLock` | 读写锁 |
| Atomic | `std::sync::atomic::AtomicUsize` | 原子操作 |
| channel | `std::sync::mpsc` / `tokio::sync::mpsc` | 消息传递 |
| Send/Sync | 编译时线程安全保证 | 编译时数据竞争检测 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| trait对象 | `dyn Trait` / `impl Trait` | 动态分发 |
| Any | `std::any::Any` / `downcast` | 运行时类型检查 |
| 宏 | `macro_rules!` / proc_macro | 编译时代码生成 |
| 依赖注入 | 无标准框架 | 通常通过trait+泛型实现 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 构建 | `cargo build` / `cargo build --release` | Cargo构建系统 |
| 包管理 | `cargo add` / crates.io | 依赖安全——`cargo audit` |
| 测试 | `cargo test` / `proptest` | 内置测试+属性测试 |
| Lint | `cargo clippy` | 官方lint |
| 安全审计 | `cargo audit` | 已知漏洞扫描 |
| unsafe检查 | `cargo geiger` | unsafe代码统计 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| 内存安全 | 安全 | 所有权+借用检查器——编译时保证 |
| 数据竞争 | 安全 | Send/Sync trait——编译时检测 |
| 空指针 | 安全 | Option<T>替代空指针 |
| 缓冲区溢出 | 安全 | 切片边界检查（运行时） |
| 整数溢出 | 安全（debug） | debug模式检查溢出，release需wrapping |
| unsafe | 需显式 | `unsafe`块需手动标记——绕过安全检查 |
| 模板转义 | 开启 | askama/tera默认autoescape |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Rust 2021 | `panic`安全改进 | 更安全的panic处理 |
| Rust 1.70+ | `OnceLock` / `OnceCell`稳定 | 惰性初始化安全 |
| Rust 1.75+ | `fn` trait in trait | 更灵活的API设计 |
| Rust 1.78+ | `#[diagnostic]`属性 | 编译诊断改进 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-MEM-BOUNDS-01 | 缓冲区溢出——unsafe块memcpy |
| vuln-patterns | VULN-MEM-INDEX-01 | 越界索引——unsafe块裸指针算术 |
| vuln-patterns | VULN-MEM-LAYOUT-01 | 内存布局——unsafe transmute |
| vuln-patterns | VULN-MEM-PTR-01 | 不可信指针——unsafe裸指针解引用 |
| vuln-patterns | VULN-CODE-UNDEF-01 | UB——unsafe块有符号溢出 |
| vuln-patterns | VULN-INJ-CMD-01 | 命令注入——Command参数拼接 |
| vuln-patterns | VULN-INJ-SSRF-01 | SSRF——reqwest可控URL |
| vuln-patterns | VULN-FILE-TRAVERSAL-01 | 路径遍历——fs::File::open拼接 |
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——format!拼接SQL |
| vuln-patterns | VULN-RES-REFCOUNT-01 | 引用计数——Rc/Arc循环引用 |
| vuln-patterns | VULN-TYPE-CAST-01 | 类型转换——unsafe transmute |
| vuln-patterns | VULN-CONC-RACE-01 | 竞态条件——unsafe绕过Send/Sync |
| attack-patterns | ATK-INJ-CMD-01 | 命令注入良性标记证明 |
| attack-patterns | ATK-INJ-SSRF-01 | SSRF良性回调探测 |
| attack-patterns | ATK-FILE-TRAVERSAL-01 | 路径遍历读取证明 |
| attack-patterns | ATK-MEM-LAYOUT-01 | 布局差异良性证明 |
| fix-patterns | FIX-MEM-BOUNDS-01 | 使用安全切片操作替代unsafe |
| fix-patterns | FIX-MEM-LAYOUT-01 | 显式序列化替代transmute |
| fix-patterns | FIX-INJ-CMD-01 | Command参数数组 |
| fix-patterns | FIX-FILE-TRAVERSAL-01 | canonicalize+starts_with |
| fix-patterns | FIX-SQLI-PARAMQUERY-01 | sqlx::query().bind() |
| fix-patterns | FIX-RES-REFCOUNT-01 | Weak引用打破循环 |

## 正例/负例

**正例**（Rust中的安全写法）：
```rust
// 参数化查询
let user = sqlx::query_as::<_, User>("SELECT * FROM users WHERE id = $1")
    .bind(user_id)
    .fetch_one(&pool)
    .await?;

// 命令执行用参数数组
let output = std::process::Command::new("ls")
    .args(["-la", &user_dir])
    .output()?;

// 路径遍历防护
let canonical = std::fs::canonicalize(base_dir.join(&filename))?;
if !canonical.starts_with(&base_dir_canonical) {
    return Err("Path traversal detected".into());
}

// 路径规范化
let safe_path = std::fs::canonicalize(path)?;

// 安全的内存操作（无需unsafe）
let slice = &buf[start..end];  // 编译时/运行时边界检查

// 锁自动释放
let _lock = mutex.lock().unwrap();
// 锁在_lock离开作用域时自动释放
```

**负例**（Rust中的不安全写法）：
```rust
// unsafe绕过边界检查
unsafe {
    let val = *buf.get_unchecked(offset);  // 无边界检查
}

// format!拼接SQL
let query = format!("SELECT * FROM users WHERE name = '{}'", name);
sqlx::query(&query).fetch_all(&pool).await?;

// transmute绕过类型系统
unsafe {
    let val: u32 = std::mem::transmute(f32_val);  // 类型双关
}

// 裸指针解引用
unsafe {
    (*raw_ptr).field = value;  // 无安全检查
}

// 命令注入
let output = std::process::Command::new("sh")
    .arg("-c")
    .arg(format!("ls {}", user_dir))
    .output()?;
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Rust技术栈
- candidate-discovery：使用Rust Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用Rust安全API/unsafe审计映射提供修复写法

## 官方来源

- 官方文档：https://www.rust-lang.org/
- Rust安全指南：https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html
- cargo audit：https://github.com/RustSec/cargo-audit
- RustSec Advisory Database：https://rustsec.org/

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Rust语言生态映射 |
