# ECMAP-JAVA：Java语言生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-JAVA |
| name | Java语言生态映射 |
| version | v0.1 |
| 适用语言/框架 | Java（JVM运行时，不含Spring——Spring见ECMAP-JAVA-SPRING） |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `pom.xml` / `build.gradle` / `build.gradle.kts` | Maven/Gradle构建文件 |
| 文件标记 | `.java`源文件 + `package`声明 | Java源码标识 |
| 文件标记 | `MANIFEST.MF` / `.jar` / `.war` | Java打包产物 |
| 依赖标记 | `javax.servlet` / `jakarta.servlet` | Servlet API依赖 |
| 运行时标记 | `target/` (Maven) / `build/` (Gradle) | 构建产物目录 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| Servlet | `@WebServlet("/path")` / `extends HttpServlet` | Servlet入口 |
| main方法 | `public static void main(String[] args)` | Java应用入口 |
| Listener | `@WebListener` / `implements ServletContextListener` | 应用生命周期监听 |
| Filter | `@WebFilter("/*")` / `implements Filter` | 过滤器注册 |
| JAX-RS | `@Path("/api")` + `@GET` / `@POST` | REST API入口 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| Filter | `implements Filter` / `@WebFilter` | Servlet过滤器链 |
| Listener | `implements ServletContextListener` | 应用事件监听 |
| Interceptor | Spring拦截器（见Spring Profile） | Spring AOP拦截 |
| 装饰器 | `@Decorator` / CDI装饰器 | Java EE装饰器模式 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 请求参数 | `request.getParameter("name")` | 攻击者可控 |
| 请求头 | `request.getHeader("X-...")` | 攻击者可控 |
| 请求体 | `request.getReader()` / `request.getInputStream()` | 攻击者可控 |
| 路径参数 | `@PathParam("id")` (JAX-RS) | 攻击者可控 |
| Cookie | `request.getCookies()` | 攻击者可控 |
| Session | `request.getSession().getAttribute("key")` | 服务端存储 |
| 系统属性 | `System.getProperty("key")` | 部分可控 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| SQL执行 | `Statement.executeQuery(sql)` / `PreparedStatement` | 注入风险（Statement拼接时） |
| 命令执行 | `Runtime.exec()` / `ProcessBuilder` | 命令注入风险 |
| 文件操作 | `new File(path)` / `Files.readAllBytes()` | 路径遍历风险 |
| 模板渲染 | JSP / Thymeleaf / FreeMarker | XSS风险 |
| 反序列化 | `ObjectInputStream.readObject()` | 反序列化RCE风险 |
| XML解析 | `DocumentBuilder.parse()` / `SAXParser` | XXE风险 |
| 网络请求 | `HttpURLConnection` / `HttpClient` | SSRF风险 |
| 代码执行 | `ScriptEngine.eval()` / `Method.invoke()` | 代码注入风险 |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| JAAS | `LoginModule` / `Subject` | Java认证授权服务 |
| Servlet安全 | `@WebServlet` + `@ServletSecurity` | 声明式安全约束 |
| web.xml | `<security-constraint>` | XML安全约束配置 |
| 注解 | `@RolesAllowed` / `@PermitAll` | JSR-250注解 |
| 自定义Filter | 鉴权Filter实现 | 手动鉴权 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 输入校验 | `Bean Validation` (`@NotNull`, `@Size`, `@Pattern`) | JSR-380验证 |
| SQL参数化 | `PreparedStatement` with `?`占位符 | 参数化查询 |
| HTML净化 | OWASP Java Encoder / Jsoup | HTML编码/净化 |
| 路径净化 | `File.getCanonicalPath()` + `startsWith()` | 规范化+前缀验证 |
| XML净化 | `XMLInputFactory.SUPPORT_DTD = false` | 禁用DTD外部实体 |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | OWASP Java Encoder `Encode.forHtml()` | HTML编码 |
| HTML属性 | `Encode.forHtmlAttribute()` | 属性编码 |
| JavaScript | `Encode.forJavaScript()` | JS编码 |
| URL | `URLEncoder.encode()` | URL编码 |
| JSP EL | `<c:out value="${...}"/>` / `fn:escapeXml` | JSP标准标签转义 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| JPA/Hibernate | `EntityManager.createQuery("SELECT u FROM User u WHERE u.name = :name")` | 命名参数安全 |
| JPA TypedQuery | `em.createQuery(cq).setParameter("name", value)` | Criteria API安全 |
| JDBC PreparedStatement | `ps.setString(1, value)` | 参数化查询安全 |
| JDBC Statement | `stmt.executeQuery("SELECT ... WHERE col = '" + value + "'")` | **危险**——SQL注入 |
| JPA Native Query | `em.createNativeQuery("SELECT ... WHERE col = ?1")` | 需手动参数化 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON | `Jackson ObjectMapper` / `Gson` | 安全（无代码执行） |
| Java序列化 | `ObjectInputStream.readObject()` | **不安全**——RCE风险 |
| XML | `DocumentBuilder` / `SAXParser` / `JAXB` | XXE风险——需禁用DTD |
| YAML | `SnakeYAML` / `Yaml.load()` | YAML反序列化RCE风险 |
| CSV | `OpenCSV` / `Apache Commons CSV` | CSV公式注入风险 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| 线程 | `Thread` / `Runnable` / `Callable` | 需注意共享状态同步 |
| 线程池 | `ExecutorService` / `ThreadPoolExecutor` | 线程池安全 |
| Lock | `ReentrantLock` / `ReadWriteLock` | 需try-finally释放 |
| synchronized | `synchronized` 关键字 | 内置锁机制 |
| CompletableFuture | `CompletableFuture.supplyAsync()` | 异步编程 |
| Atomic | `AtomicInteger` / `AtomicReference` | 原子操作 |
| volatile | `volatile` 关键字 | 内存可见性 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 反射 | `Class.forName()` / `Method.invoke()` | 动态调用风险——类名来自外部需白名单 |
| ClassLoader | `ClassLoader.loadClass()` / `URLClassLoader` | 动态加载风险 |
| 动态代理 | `Proxy.newProxyInstance()` | 动态代理 |
| 注解处理 | `@Retention` / `@Target` | 编译时/运行时注解 |
| 代码生成 | `ASM` / `ByteBuddy` / `Javassist` | 字节码操作 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 构建工具 | Maven (`pom.xml`) / Gradle (`build.gradle`) | 构建配置安全 |
| 包管理 | Maven Central / JCenter | 依赖安全——需校验来源 |
| 测试框架 | JUnit 5 / TestNG / Mockito | 测试集成 |
| 静态分析 | SpotBugs / FindSecBugs / SonarQube | 安全专项分析 |
| 依赖扫描 | OWASP Dependency-Check / Snyk | SCA扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| JSP EL转义 | 需配置 | 需用`<c:out>`或`fn:escapeXml` |
| 序列化安全性 | 不安全 | `ObjectInputStream`默认不限制类型 |
| XML安全性 | 不安全 | XML解析器默认启用DTD/外部实体 |
| 类型安全 | 安全 | 静态类型系统提供编译时检查 |
| 内存安全 | 安全 | JVM提供内存安全（无缓冲区溢出） |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Java 17 LTS | `ObjectInputFilter`内置 | 反序列化过滤 |
| Java 11+ | `HttpClient`新API | HTTP客户端替代 |
| Java 8+ | `BigInteger`/`String`安全改进 | 字符串处理改进 |
| Jakarta EE 9+ | `javax.*` → `jakarta.*`命名空间迁移 | 依赖迁移 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——Statement拼接 |
| vuln-patterns | VULN-INJ-CMD-01 | 命令注入——Runtime.exec |
| vuln-patterns | VULN-INJ-DESERIAL-01 | 反序列化——ObjectInputStream.readObject |
| vuln-patterns | VULN-INJ-XXE-01 | XXE——DocumentBuilder默认启用外部实体 |
| vuln-patterns | VULN-INJ-SSRF-01 | SSRF——HttpClient可控URL |
| vuln-patterns | VULN-FILE-TRAVERSAL-01 | 路径遍历——new File拼接 |
| vuln-patterns | VULN-CALC-COMPARE-01 | 比较错误——==比较字符串引用 |
| vuln-patterns | VULN-CONC-RACE-01 | 竞态条件——synchronized使用不当 |
| vuln-patterns | VULN-CONC-LOCKING-01 | 锁使用不当——未try-finally释放 |
| vuln-patterns | VULN-EXC-UNCHECKED-01 | 返回值未检查 |
| vuln-patterns | VULN-ENCAP-INSUFFICIENT-01 | 封装不足——public字段暴露 |
| vuln-patterns | VULN-INFO-STORAGE-01 | 硬编码密钥 |
| vuln-patterns | VULN-MEM-LAYOUT-01 | 内存布局依赖（JNI/unsafe） |
| attack-patterns | ATK-INJ-DESERIAL-01 | 反序列化良性gadget证明 |
| attack-patterns | ATK-INJ-XXE-01 | XXE良性外部实体读取证明 |
| attack-patterns | ATK-CALC-COMPARE-01 | 比较错误绕过良性证明 |
| attack-patterns | ATK-CONC-RACE-01 | 竞态条件良性证明 |
| attack-patterns | ATK-CONC-LOCKING-01 | 死锁良性证明 |
| attack-patterns | ATK-ENCAP-INSUFFICIENT-01 | 封装不足良性探测 |
| fix-patterns | FIX-SQLI-PARAMQUERY-01 | PreparedStatement参数化 |
| fix-patterns | FIX-INJ-DESERIAL-01 | ObjectInputFilter类型白名单 |
| fix-patterns | FIX-INJ-XXE-01 | 禁用DTD外部实体 |
| fix-patterns | FIX-FILE-TRAVERSAL-01 | getCanonicalPath+startsWith |
| fix-patterns | FIX-CONC-LOCKING-01 | try-finally锁释放 |
| fix-patterns | FIX-CALC-COMPARE-01 | String.equals替代== |
| fix-patterns | FIX-ENCAP-INSUFFICIENT-01 | private字段+不可变返回 |

## 正例/负例

**正例**（Java中的安全写法）：
```java
// PreparedStatement参数化
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
ps.setInt(1, userId);
ResultSet rs = ps.executeQuery();

// 反序列化过滤
ObjectInputStream ois = new ObjectInputStream(in);
ois.setObjectInputFilter(filterInfo -> {
    if (filterInfo.serialClass() != null &&
        filterInfo.serialClass().getName().startsWith("com.example.")) {
        return ObjectInputFilter.Status.ALLOWED;
    }
    return ObjectInputFilter.Status.REJECTED;
});

// XXE防护
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setXIncludeAware(false);
dbf.setExpandEntityReferences(false);

// 路径遍历防护
File f = new File(baseDir, fileName);
String canonicalPath = f.getCanonicalPath();
if (!canonicalPath.startsWith(baseDir.getCanonicalPath())) {
    throw new SecurityException("Path traversal detected");
}

// 字符串比较用equals
if (input.equals(expected)) { ... }
```

**负例**（Java中的不安全写法）：
```java
// Statement拼接
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE name = '" + name + "'");

// 不安全反序列化
ObjectInputStream ois = new ObjectInputStream(in);
Object obj = ois.readObject();

// XXE默认行为
DocumentBuilder db = DocumentBuilderFactory.newInstance().newDocumentBuilder();
Document doc = db.parse(userXml);  // 默认启用外部实体

// 命令注入
Runtime.getRuntime().exec("ping " + userInput);

// ==比较字符串
if (input == "expected") { ... }  // 比较引用而非值

// 锁未在try-finally中释放
lock.lock();
doSomething();  // 如果抛异常，锁不会释放
lock.unlock();
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Java技术栈
- candidate-discovery：使用Java Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用Java安全API/Encoder映射提供修复写法

## 官方来源

- 官方文档：https://docs.oracle.com/en/java/
- 安全指南：https://www.oracle.com/java/technologies/javase/seccodeguide.html
- OWASP Java Encoder：https://github.com/OWASP/owasp-java-encoder
- FindSecBugs：https://find-sec-bugs.github.io/

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Java语言生态映射 |
