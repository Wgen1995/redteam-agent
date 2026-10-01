# ECMAP-CSHARP-DOTNET：C#/.NET生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-CSHARP-DOTNET |
| name | C#/.NET生态映射 |
| version | v0.1 |
| 适用语言/框架 | C# / .NET / ASP.NET Core |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `.csproj` / `.sln` / `global.json` | .NET项目/解决方案文件 |
| 文件标记 | `.cs`源文件 / `Program.cs` 入口 | C#源码标识 |
| 文件标记 | `appsettings.json` / `web.config` | .NET配置文件 |
| 框架标记 | `using Microsoft.AspNetCore` / `using System.Web` | ASP.NET导入 |
| 框架标记 | `[ApiController]` / `[Controller]` | ASP.NET Core控制器 |
| 依赖标记 | `Microsoft.AspNetCore.*` / `System.Data.*` in `.csproj` | .NET依赖 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| 控制器路由 | `[HttpGet("/path")]` / `[Route("api/[controller]")]` | ASP.NET Core属性路由 |
| 约定路由 | `app.UseEndpoints(e => e.MapControllerRoute(...))` | 约定式路由 |
| Minimal API | `app.MapGet("/path", handler)` | .NET 6+ Minimal API |
| 路径参数 | `[HttpGet("/user/{id}")]` + `int id` 参数 | 路径参数绑定 |
| Main | `static void Main(string[] args)` / 顶级语句 | C#程序入口 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| 中间件 | `app.Use(async (ctx, next) => { ... await next(); })` | 自定义中间件 |
| 内置中间件 | `UseAuthentication()` / `UseAuthorization()` / `UseCors()` | ASP.NET Core内置 |
| 过滤器 | `IAuthorizationFilter` / `IActionFilter` | MVC过滤器 |
| 异常处理 | `UseExceptionHandler()` / `IExceptionFilter` | 全局异常处理 |
| 模型验证 | `[ApiController]`自动验证 / `IModelValidator` | 自动模型验证 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 查询参数 | `[FromQuery] string param` / `Request.Query["param"]` | 攻击者可控 |
| 路径参数 | `[FromRoute] int id` | 攻击者可控 |
| 请求体 | `[FromBody] UserDTO dto` | 攻击者可控（经模型验证） |
| 请求头 | `[FromHeader] string token` / `Request.Headers["X-..."]` | 攻击者可控 |
| 表单 | `[FromForm] string name` / `Request.Form["name"]` | 攻击者可控 |
| Cookie | `Request.Cookies["name"]` | 攻击者可控 |
| 文件上传 | `IFormFile file` | 攻击者可控 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| EF Core | `context.Users.Where(u => u.Name == name)` | 安全（LINQ参数化） |
| FromSqlRaw | `context.Users.FromSqlRaw("SELECT ... WHERE col = {0}", value)` | 需参数化 |
| FromSqlInterpolated | `context.Users.FromSqlInterpolated($"SELECT ... WHERE col = {value}")` | 安全（插值参数化） |
| ADO.NET | `command.Parameters.AddWithValue("@col", value)` | 参数化——安全 |
| 命令执行 | `Process.Start(fileName, args)` | 命令注入风险 |
| 文件操作 | `File.ReadAllText(path)` / `Path.Combine(dir, name)` | 路径遍历风险 |
| 模板渲染 | Razor Pages / Razor Views | Razor默认编码 |
| 反序列化 | `JsonConvert.DeserializeObject()` / `BinaryFormatter.Deserialize()` | BinaryFormatter不安全 |
| XML | `XmlDocument.Load()` / `XmlReader.Create()` | XXE风险 |
| 网络 | `HttpClient.GetAsync(url)` | SSRF风险 |
| 重定向 | `Redirect(url)` / `RedirectResult` | 开放重定向风险 |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| [Authorize] | `[Authorize]` / `[Authorize(Roles = "Admin")]` | 声明式授权 |
| [AllowAnonymous] | `[AllowAnonymous]` | 允许匿名访问 |
| 策略授权 | `[Authorize(Policy = "RequireAdmin")]` | 基于策略的授权 |
| 认证中间件 | `builder.Services.AddAuthentication()` | 认证服务注册 |
| JWT | `AddJwtBearer()` | JWT Bearer认证 |
| Identity | `AddIdentity<User, Role>()` | ASP.NET Core Identity |
| Claims | `User.Claims` / `User.IsInRole("Admin")` | 基于声明的授权 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 数据注解 | `[Required]` / `[StringLength(100)]` / `[RegularExpression]` | 声明式验证 |
| FluentValidation | `AbstractValidator<T>` | 流式验证 |
| SQL参数化 | `SqlParameter` / EF Core LINQ | 参数化查询 |
| HTML净化 | `HtmlSanitizer` NuGet包 | HTML净化 |
| 路径净化 | `Path.GetFullPath()` + `StartsWith()` | 规范化+前缀验证 |
| 命令参数 | `ProcessStartInfo.ArgumentList.Add(arg)` | 参数数组（.NET 5+） |
| 防伪令牌 | `[ValidateAntiForgeryToken]` / `AddAntiforgery()` | CSRF防护 |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | Razor `@value` 自动编码 | Razor默认HTML编码 |
| HTML属性 | Razor `@value` 自动编码 | 自动处理 |
| JavaScript | Razor `@value` 在JS上下文 | 上下文感知编码 |
| URL | `Uri.EscapeDataString()` / `UrlEncoder` | URL编码 |
| 不转义 | Razor `@Html.Raw(value)` | **危险**——不编码输出 |
| AntiXSS | `System.Web.Security.AntiXss` (legacy) | 编码库（已集成到.NET Core） |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| EF Core LINQ | `context.Users.Where(u => u.Name == name)` | 参数化——安全 |
| EF Core FromSqlRaw | `context.Users.FromSqlRaw("SELECT ... WHERE col = {0}", value)` | 需参数化 |
| EF Core FromSqlInterpolated | `context.Users.FromSqlInterpolated($"SELECT ... WHERE col = {value}")` | 安全（插值自动参数化） |
| Dapper | `connection.Query<User>("SELECT ... WHERE col = @col", new { col = value })` | 参数化——安全 |
| ADO.NET | `cmd.CommandText = "SELECT ... WHERE col = @col"; cmd.Parameters.AddWithValue("@col", value)` | 参数化——安全 |
| ADO.NET拼接 | `cmd.CommandText = "SELECT ... WHERE col = '" + value + "'"` | **危险**——SQL拼接 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON | `System.Text.Json.JsonSerializer` / `JsonConvert` | 安全 |
| BinaryFormatter | `BinaryFormatter.Deserialize()` | **不安全**——RCE风险（.NET 5+已废弃） |
| XML | `XmlSerializer` / `XmlDocument` | XXE风险——需禁用DTD |
| DataContract | `DataContractSerializer` | 安全 |
| Protocol Buffers | `protobuf-net` | 安全 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| async/await | `async Task<ActionResult>` / `await` | 异步控制器 |
| Task | `Task.Run()` / `Task.WhenAll()` | 任务并行 |
| Concurrent Collections | `ConcurrentDictionary` / `ConcurrentQueue` | 线程安全集合 |
| lock | `lock(obj) { ... }` | 互斥锁——自动释放 |
| Monitor | `Monitor.Enter()` / `Monitor.Exit()` | 手动锁 |
| SemaphoreSlim | `await semaphore.WaitAsync()` | 异步信号量 |
| Interlocked | `Interlocked.Increment()` / `Interlocked.CompareExchange()` | 原子操作 |
| CancellationToken | `CancellationToken` | 取消传播 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 反射 | `Type.GetType()` / `Activator.CreateInstance()` | 类型名来自外部需白名单 |
| 依赖注入 | `services.AddScoped<IService, Service>()` | ASP.NET Core内置DI |
| 属性注入 | `[FromServices] IService service` | 属性注入 |
| 动态代码 | `System.Reflection.Emit` / `Roslyn` | 动态代码生成 |
| Source Generator | `ISourceGenerator` | 编译时代码生成 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 构建 | `dotnet build` / `dotnet publish` | .NET CLI |
| 包管理 | NuGet (`nuget.org`) | 依赖安全 |
| 测试 | xUnit / NUnit / MSTest | 测试框架 |
| 静态分析 | Roslyn Analyzer / SonarQube / Puma Scan | 安全分析 |
| 依赖扫描 | `dotnet list package --vulnerable` | 内置漏洞扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| Razor编码 | 开启 | Razor `@`默认HTML编码 |
| 模型验证 | 开启（ApiController） | `[ApiController]`自动验证 |
| CSRF防护 | 需配置 | 需`AddAntiforgery()`+`[ValidateAntiForgeryToken]` |
| HTTPS | 需配置 | `UseHttpsRedirection()`需手动 |
| BinaryFormatter | 废弃 | .NET 5+已废弃——避免使用 |
| 内存安全 | 安全 | CLR提供GC和类型安全 |
| 异常详情 | 需关闭 | 生产环境`DeveloperExceptionPage`禁用 |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| .NET 8 LTS | `CompositeFormat` | 更安全的格式化 |
| .NET 7+ | `Metrics` API | 安全监控 |
| .NET 6+ | BinaryFormatter废弃 | 反序列化安全 |
| .NET 5+ | `ArgumentNullException.ThrowIfNull` | 更简洁的参数验证 |
| ASP.NET Core 8 | RateLimiter中间件 | 内置速率限制 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——FromSqlRaw或ADO.NET拼接 |
| vuln-patterns | VULN-INJ-CMD-01 | 命令注入——Process.Start拼接 |
| vuln-patterns | VULN-INJ-DESERIAL-01 | 反序列化——BinaryFormatter.Deserialize |
| vuln-patterns | VULN-INJ-XXE-01 | XXE——XmlDocument默认启用外部实体 |
| vuln-patterns | VULN-INJ-SSRF-01 | SSRF——HttpClient可控URL |
| vuln-patterns | VULN-FILE-TRAVERSAL-01 | 路径遍历——Path.Combine拼接 |
| vuln-patterns | VULN-XSS-AUTOESCAPE-01 | XSS——@Html.Raw不编码 |
| vuln-patterns | VULN-CRYPTO-NOORIGIN-01 | CSRF——缺[ValidateAntiForgeryToken] |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权缺失——无[Authorize] |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——Redirect可控URL |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 信息泄露——DeveloperExceptionPage暴露堆栈 |
| vuln-patterns | VULN-RES-FREQUENCY-01 | 速率限制缺失——无RateLimiter |
| attack-patterns | ATK-SQLI-BENIGN-01 | 良性SQL注入标记证明 |
| attack-patterns | ATK-INJ-CMD-01 | 良性命令注入标记证明 |
| attack-patterns | ATK-INJ-DESERIAL-01 | 良性反序列化gadget证明 |
| attack-patterns | ATK-INJ-XXE-01 | 良性XXE读取证明 |
| attack-patterns | ATK-CRYPTO-CSRF-01 | CSRF良性标记证明 |
| attack-patterns | ATK-AUTHZ-DUAL-IDENTITY-01 | 双身份授权缺失证明 |
| fix-patterns | FIX-SQLI-PARAMQUERY-01 | EF Core LINQ / FromSqlInterpolated |
| fix-patterns | FIX-INJ-DESERIAL-01 | 替代BinaryFormatter |
| fix-patterns | FIX-INJ-XXE-01 | XmlReaderSettings禁用DTD |
| fix-patterns | FIX-CRYPTO-ORIGIN-01 | AddAntiforgery+[ValidateAntiForgeryToken] |
| fix-patterns | FIX-AUTHZ-ADDCHECK-01 | 添加[Authorize] |
| fix-patterns | FIX-RES-FREQUENCY-01 | RateLimiter中间件 |

## 正例/负例

**正例**（C#/.NET中的安全写法）：
```csharp
// EF Core LINQ（参数化）
var user = await _context.Users
    .Where(u => u.Name == name)
    .FirstOrDefaultAsync();

// FromSqlInterpolated（自动参数化）
var users = _context.Users
    .FromSqlInterpolated($"SELECT * FROM users WHERE name = {name}")
    .ToList();

// [Authorize] + [ValidateAntiForgeryToken]
[Authorize(Roles = "Admin")]
[HttpPost]
[ValidateAntiForgeryToken]
public IActionResult DeleteUser(int id) { ... }

// 路径遍历防护
var fullPath = Path.GetFullPath(Path.Combine(baseDir, fileName));
if (!fullPath.StartsWith(baseDirFullPath))
    return Forbid();

// Razor编码
// @Model.UserName  ← 自动HTML编码

// XXE防护
var settings = new XmlReaderSettings {
    DtdProcessing = DtdProcessing.Prohibit
};
using var reader = XmlReader.Create(stream, settings);
```

**负例**（C#/.NET中的不安全写法）：
```csharp
// SQL拼接
cmd.CommandText = "SELECT * FROM users WHERE name = '" + name + "'";

// FromSqlRaw拼接
var users = _context.Users.FromSqlRaw($"SELECT * FROM users WHERE name = '{name}'");

// @Html.Raw不编码
// @Html.Raw(Model.UserInput)

// BinaryFormatter
var obj = (MyClass)new BinaryFormatter().Deserialize(stream);

// 无[Authorize]
[HttpPost]
public IActionResult DeleteUser(int id) { ... }

// 重定向无验证
return Redirect(Request.Query["redirectUrl"]);

// XXE默认
var doc = new XmlDocument();
doc.Load(userXml);  // 默认启用DTD外部实体
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用C#/.NET技术栈
- candidate-discovery：使用C# Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用.NET安全API/中间件配置提供修复写法

## 官方来源

- 官方文档：https://learn.microsoft.com/dotnet/
- ASP.NET Core安全：https://learn.microsoft.com/aspnet/core/security/
- EF Core：https://learn.microsoft.com/ef/core/
- .NET安全博客：https://devblogs.microsoft.com/dotnet/category/security/

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——C#/.NET生态映射 |
