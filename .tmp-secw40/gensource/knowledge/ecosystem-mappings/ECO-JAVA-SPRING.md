# ECMAP-JAVA-SPRING：Spring框架生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-JAVA-SPRING |
| name | Spring框架生态映射 |
| version | v0.1 |
| 适用语言/框架 | Java + Spring Framework / Spring Boot |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `pom.xml`含`spring-boot-starter` / `build.gradle`含`spring-boot` | Spring Boot依赖 |
| 文件标记 | `application.properties` / `application.yml` | Spring Boot配置文件 |
| 框架标记 | `@SpringBootApplication` / `@RestController` / `@Controller` | Spring注解 |
| 框架标记 | `@GetMapping` / `@PostMapping` / `@RequestMapping` | Spring MVC路由 |
| 框架标记 | `@Service` / `@Repository` / `@Component` / `@Autowired` | Spring DI注解 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| 控制器路由 | `@GetMapping("/path")` / `@RequestMapping("/path")` | Spring MVC路由 |
| 路径参数 | `@GetMapping("/user/{id}")` + `@PathVariable Long id` | 路径变量捕获 |
| RestController | `@RestController` + `@RequestMapping("/api")` | REST API控制器 |
| WebSocket | `@MessageMapping("/ws")` | Spring WebSocket |
| Actuator | `management.endpoints.web.exposure.include` | Actuator端点 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| HandlerInterceptor | `implements HandlerInterceptor` | Spring MVC拦截器 |
| Filter | `implements Filter` / `FilterRegistrationBean` | Servlet过滤器 |
| @ControllerAdvice | `@ControllerAdvice` / `@RestControllerAdvice` | 全局异常处理 |
| Security Filter Chain | `SecurityFilterChain` Bean | Spring Security过滤器链 |
| AOP | `@Aspect` / `@Pointcut` / `@Around` | AOP切面 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 请求参数 | `@RequestParam("name") String name` | 攻击者可控 |
| 路径参数 | `@PathVariable Long id` | 攻击者可控 |
| 请求体 | `@RequestBody UserDTO dto` | 攻击者可控 |
| 请求头 | `@RequestHeader("X-...") String header` | 攻击者可控 |
| Cookie | `@CookieValue("session") String session` | 攻击者可控 |
| Model属性 | `Model.addAttribute("key", value)` | 服务端存储但渲染时可控 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| JPA查询 | `repository.findByname(name)` / `@Query` | 安全（派生查询） |
| JPQL | `@Query("SELECT u FROM User u WHERE u.name = :name")` | 需命名参数 |
| 原生SQL | `@Query(value="SELECT * FROM users WHERE name = ?1", nativeQuery=true)` | 需位置参数 |
| 模板渲染 | `ModelAndView` / Thymeleaf / FreeMarker | XSS风险（需autoescape） |
| 重定向 | `redirect:url` / `RedirectView` | 开放重定向风险 |
| 文件操作 | `FileCopyUtils` / `Resource` | 路径遍历风险 |
| SpEL | `@Value("#{...}")` / `SpelExpressionParser` | SpEL注入风险 |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| Spring Security | `@EnableWebSecurity` + `SecurityFilterChain` | Spring Security配置 |
| 方法级安全 | `@PreAuthorize("hasRole('ADMIN')")` | 方法级授权 |
| `@Secured` | `@Secured("ROLE_ADMIN")` | JSR-250注解 |
| `@RolesAllowed` | `@RolesAllowed("ADMIN")` | JSR-250标准 |
| SecurityContext | `SecurityContextHolder.getContext().getAuthentication()` | 当前认证信息 |
| CSRF | `CsrfToken` / `@EnableWebSecurity` CSRF配置 | Spring Security CSRF防护 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| Bean Validation | `@Valid` + `@NotNull`, `@Size`, `@Pattern` | JSR-380验证 |
| 输入校验 | `@Validated` + `Validator` | Spring验证 |
| SQL参数化 | JPA命名参数 / `@Query` with `?1` | 参数化查询 |
| HTML净化 | OWASP Java Encoder / Jsoup `safelist()` | HTML编码/净化 |
| Thymeleaf转义 | Thymeleaf `th:text` 默认转义 | `th:utext`为不转义（危险） |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | Thymeleaf `th:text` / `[[${...}]]` | 默认HTML转义 |
| HTML属性 | Thymeleaf属性值自动转义 | 需确保引号转义 |
| JavaScript | Thymeleaf `th:inline="javascript"` | JS内联转义 |
| URL | Thymeleaf `@{...}` URL表达式 | URL编码 |
| 不转义 | `th:utext` / `[(...)]` | **危险**——不转义输出 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| Spring Data JPA | `Repository.findByname(name)` | 派生查询安全（参数化） |
| @Query JPQL | `@Query("SELECT u FROM User u WHERE u.name = :name")` | 需命名参数 |
| @Query native | `@Query(value="SELECT * FROM users WHERE name = ?1", nativeQuery=true)` | 需位置参数 |
| EntityManager | `em.createQuery("SELECT u FROM User u WHERE u.name = :name").setParameter("name", value)` | 需命名参数 |
| JdbcTemplate | `jdbcTemplate.queryForObject("SELECT ... WHERE col = ?", String.class, value)` | 需参数化 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| Jackson | `ObjectMapper.readValue()` / `@JsonIgnore` | 安全（无代码执行），注意`@JsonIgnore`排除敏感字段 |
| JSON视图 | `@JsonView` / `@JsonProperty` | 控制序列化字段 |
| Java序列化 | `ObjectInputStream` | 不安全——避免使用 |
| XML | `JAXB` / `Jackson XML` | XXE风险 |
| YAML | `SnakeYAML` / `@ConfigurationProperties` | YAML反序列化风险 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| @Async | `@Async` / `ThreadPoolTaskExecutor` | 异步方法执行 |
| CompletableFuture | `CompletableFuture.supplyAsync()` | 异步组合 |
| Reactor | `Mono` / `Flux` (WebFlux) | 响应式编程 |
| @Scheduled | `@Scheduled(fixedRate=...)` | 定时任务 |
| 事务 | `@Transactional` | 事务管理——注意隔离级别 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 依赖注入 | `@Autowired` / `@Inject` / 构造器注入 | Spring核心DI |
| 组件扫描 | `@ComponentScan` | 自动组件发现 |
| SpEL | `SpelExpressionParser` / `@Value("#{...}")` | SpEL注入风险——表达式来自外部时 |
| AOP | `@Aspect` / `@Pointcut` | AOP切面编程 |
| 条件装配 | `@Conditional` / `@Profile` | 条件化Bean装配 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 构建 | Maven / Gradle | 构建配置 |
| Spring Boot | `spring-boot-maven-plugin` | 可执行JAR打包 |
| 测试 | `@SpringBootTest` / `@WebMvcTest` / `MockMvc` | Spring测试 |
| Actuator | `management.endpoints` | 生产环境需限制暴露端点 |
| 依赖扫描 | OWASP Dependency-Check / Snyk | SCA扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| Thymeleaf转义 | 开启 | `th:text`默认HTML转义 |
| Spring Security CSRF | 开启（启用Security时） | CSRF token默认启用 |
| Spring Security会话 | 可配置 | 会话固定保护默认 |
| Actuator端点 | 需限制 | 默认仅`health`和`info`暴露 |
| H2控制台 | 禁用 | 生产环境必须关闭 |
| 白标签错误页 | 需关闭 | `server.error.whitelabel.enabled=false` |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Spring Boot 3.x | `javax.*` → `jakarta.*` 迁移 | 依赖迁移 |
| Spring Security 6.x | `WebSecurityConfigurerAdapter`废弃 | Lambda DSL配置 |
| Spring Boot 2.7+ | Security配置方式变更 | SecurityFilterChain Bean |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-CRYPTO-NOORIGIN-01 | CSRF——禁用CSRF或`permitAll()` |
| vuln-patterns | VULN-XSS-AUTOESCAPE-01 | XSS——Thymeleaf `th:utext`不转义 |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权缺失——无`@PreAuthorize` |
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——@Query拼接 |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——`redirect:`可控 |
| vuln-patterns | VULN-STATE-EXTCONTROL-01 | Mass assignment——@ModelAttribute绑定全部字段 |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 信息泄露——Actuator端点暴露 |
| vuln-patterns | VULN-PROT-CLIENTSIDE-01 | 客户端控制——前端隐藏但API无权限 |
| vuln-patterns | VULN-EXC-FAILOPEN-01 | fail-open——Security异常处理不当 |
| vuln-patterns | VULN-SPHERE-ALTPATH-01 | 替代路径——Actuator端点无认证 |
| attack-patterns | ATK-CRYPTO-CSRF-01 | CSRF良性标记证明 |
| attack-patterns | ATK-XSS-BENIGN-DOM-01 | XSS良性DOM标记证明 |
| attack-patterns | ATK-AUTHZ-DUAL-IDENTITY-01 | 双身份授权缺失证明 |
| attack-patterns | ATK-STATE-EXTCONTROL-01 | Mass assignment良性探测 |
| attack-patterns | ATK-INFO-EXPOSURE-01 | Actuator端点暴露探测 |
| attack-patterns | ATK-SPHERE-ALTPATH-01 | 替代路径良性探测 |
| fix-patterns | FIX-CRYPTO-ORIGIN-01 | CSRF防护修复 |
| fix-patterns | FIX-XSS-AUTOESCAPE-01 | 恢复Thymeleaf转义 |
| fix-patterns | FIX-AUTHZ-ADDCHECK-01 | 添加@PreAuthorize |
| fix-patterns | FIX-STATE-EXTCONTROL-01 | DTO字段白名单 |
| fix-patterns | FIX-INFO-EXPOSURE-01 | 限制Actuator端点 |

## 正例/负例

**正例**（Spring中的安全写法）：
```java
// 方法级授权
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/users/{id}")
public void deleteUser(@PathVariable Long id) { ... }

// JPA参数化
@Query("SELECT u FROM User u WHERE u.name = :name")
User findByName(@Param("name") String name);

// Thymeleaf转义
// <span th:text="${userInput}">placeholder</span>

// CSRF默认启用
http.csrf().csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse());

// DTO白名单
public class UserDTO {
    private String username;
    @JsonIgnore
    private String password;  // 不序列化
}
```

**负例**（Spring中的不安全写法）：
```java
// 无授权检查
@DeleteMapping("/users/{id}")
public void deleteUser(@PathVariable Long id) { ... }

// @Query拼接
@Query("SELECT u FROM User u WHERE u.name = '" + name + "'")

// th:utext不转义
// <span th:utext="${userInput}">placeholder</span>

// 禁用CSRF
http.csrf().disable();

// @ModelAttribute绑定全部
@PostMapping("/users")
public User create(@ModelAttribute User user) { ... }  // 绑定isAdmin字段

// Actuator全暴露
// management.endpoints.web.exposure.include=*
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Spring框架
- candidate-discovery：使用Spring Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用Spring Security/API配置提供修复写法

## 官方来源

- 官方文档：https://docs.spring.io/spring-boot/
- Spring Security：https://docs.spring.io/spring-security/
- 安全指南：https://docs.spring.io/spring-security/reference/exploits/

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Spring框架生态映射 |
