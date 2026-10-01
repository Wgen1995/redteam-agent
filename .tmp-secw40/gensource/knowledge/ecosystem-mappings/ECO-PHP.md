# ECMAP-PHP：PHP语言生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-PHP |
| name | PHP语言生态映射 |
| version | v0.1 |
| 适用语言/框架 | PHP（Zend运行时，不含Laravel——Laravel见ECMAP-PHP-LARAVEL） |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `composer.json` / `composer.lock` | PHP项目依赖清单 |
| 文件标记 | `.php`源文件 + `<?php`标签 | PHP源码标识 |
| 文件标记 | `php.ini` 配置文件 | PHP运行时配置 |
| 框架标记 | `index.php` 前端控制器 | PHP入口文件 |
| 运行时标记 | `vendor/` 目录（Composer） | Composer依赖目录 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| 脚本入口 | `index.php` 直接执行 | PHP脚本直接执行 |
| 路由包含 | `include 'controller.php'` / `require` | 文件包含路由 |
| 自动加载 | `spl_autoload_register()` / Composer autoload | 自动类加载 |
| CLI | `php script.php` / `$argv` | 命令行入口 |
| Web服务器 | `$_SERVER['REQUEST_METHOD']` | Web请求处理 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| 自动前置 | `auto_prepend_file` in php.ini | 自动前置文件 |
| 输出缓冲 | `ob_start()` / `ob_end_flush()` | 输出缓冲控制 |
| 错误处理 | `set_error_handler()` / `set_exception_handler()` | 自定义错误处理 |
| 过滤器 | `filter_var()` / `filter_input()` | PHP内置过滤器 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| GET参数 | `$_GET['param']` / `$_GET` | 攻击者可控 |
| POST参数 | `$_POST['param']` / `$_POST` | 攻击者可控 |
| 请求 | `$_REQUEST['param']`（GET+POST+COOKIE） | 攻击者可控 |
| 请求头 | `$_SERVER['HTTP_X_...']` / `getallheaders()` | 攻击者可控 |
| Cookie | `$_COOKIE['name']` | 攻击者可控 |
| 文件上传 | `$_FILES['file']` | 攻击者可控 |
| 路径信息 | `$_SERVER['PATH_INFO']` | 攻击者可控 |
| 服务器变量 | `$_SERVER['REQUEST_URI']` | 攻击者可控 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| SQL执行 | `mysqli_query()` / `PDO::query()` / `pg_query()` | 注入风险（拼接时） |
| 命令执行 | `system()` / `exec()` / `shell_exec()` / `passthru()` | 命令注入风险 |
| 文件操作 | `fopen()` / `include()` / `require()` / `file_get_contents()` | 路径遍历/LFI风险 |
| 代码执行 | `eval()` / `create_function()` / `preg_replace(/e)` | 代码注入风险 |
| 输出 | `echo` / `print` / `printf()` | XSS风险（原生输出） |
| 反序列化 | `unserialize()` | 反序列化RCE风险 |
| 模板渲染 | 原生PHP `<?php echo $var; ?>` | XSS风险 |
| 网络请求 | `file_get_contents(url)` / `curl_exec()` | SSRF风险 |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| Session | `session_start()` / `$_SESSION['user_id']` | PHP内置会话 |
| HTTP认证 | `$_SERVER['PHP_AUTH_USER']` | HTTP Basic/Digest认证 |
| 自定义鉴权 | `if (!is_authenticated()) { header('Location: /login'); exit; }` | 手动鉴权 |
| 过滤器 | `filter_input(INPUT_POST, 'param', FILTER_VALIDATE_INT)` | 输入过滤 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 输入校验 | `filter_var()` / `filter_input()` with `FILTER_VALIDATE_*` | PHP内置验证 |
| 输入净化 | `filter_var()` with `FILTER_SANITIZE_*` | PHP内置净化 |
| SQL参数化 | `mysqli_prepare()` / `PDO::prepare()` with `?`占位符 | 参数化查询 |
| HTML净化 | `htmlspecialchars()` | HTML实体编码 |
| 命令净化 | `escapeshellarg()` / `escapeshellcmd()` | shell参数转义 |
| 路径净化 | `realpath()` + `strpos()`检查 | 规范化+前缀验证 |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | `htmlspecialchars($val, ENT_QUOTES, 'UTF-8')` | HTML实体编码 |
| HTML属性 | `htmlspecialchars($val, ENT_QUOTES, 'UTF-8')` | 需转义引号 |
| JavaScript | `json_encode($val, JSON_HEX_TAG)` | JSON编码用于JS |
| URL | `urlencode()` / `rawurlencode()` | URL编码 |
| 不转义 | `echo $val;` | **危险**——原生输出不转义 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| PDO预处理 | `$stmt = $pdo->prepare("SELECT ... WHERE col = ?"); $stmt->execute([$value]);` | 参数化——安全 |
| mysqli预处理 | `$stmt = $mysqli->prepare("SELECT ... WHERE col = ?"); $stmt->bind_param("s", $value);` | 参数化——安全 |
| PDO query | `$pdo->query("SELECT ... WHERE col = '" . $value . "'")` | **危险**——SQL拼接 |
| mysqli query | `mysqli_query($conn, "SELECT ... WHERE col = '" . $value . "'")` | **危险**——SQL拼接 |
| Eloquent | Laravel ORM（见Laravel Profile） | 参数化默认开启 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON | `json_encode()` / `json_decode()` | 安全 |
| PHP序列化 | `serialize()` / `unserialize()` | **不安全**——`unserialize`可触发__wakeup/__destruct |
| XML | `SimpleXML` / `DOMDocument` | XXE风险——需禁用外部实体 |
| CSV | `fgetcsv()` / `str_getcsv()` | CSV公式注入风险 |
| 文件包含 | `include` / `require` | LFI/RFI风险——不包含外部输入 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| 同步模型 | PHP默认同步请求处理 | 每请求独立进程 |
| FPM | PHP-FPM进程管理 | 进程池隔离 |
| ReactPHP | `React\EventLoop` | 异步事件循环 |
| Swoole | `Swoole\Coroutine` | 协程异步 |
| 锁 | `flock()` / Redis锁 | 文件锁/分布式锁 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 反射 | `ReflectionClass` / `ReflectionMethod` | 动态类/方法检查 |
| 动态调用 | `call_user_func()` / `call_user_func_array()` | 函数名来自外部需白名单 |
| 动态属性 | `$obj->$propname` | 属性名来自外部需白名单 |
| 变量变量 | `$$varname` | **危险**——变量名来自外部 |
| 类自动加载 | `spl_autoload_register()` | 类名来自外部需注意 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 包管理 | Composer (`composer.json`) | 依赖安全——`composer audit` |
| 测试框架 | PHPUnit / Pest | 测试集成 |
| 静态分析 | PHPStan / Psalm | 类型安全分析 |
| Lint工具 | PHP_CodeSniffer / PHP-CS-Fixer | 代码规范 |
| 依赖扫描 | `composer audit` / roave/security-advisories | SCA扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| 输出转义 | 不安全 | `echo`不自动转义——需`htmlspecialchars` |
| magic_quotes | 废弃（PHP 5.4+移除） | 不再自动转义输入 |
| SQL参数化 | 需手动 | 需用PDO/mysqli预处理 |
| 文件包含 | 不安全 | `include`不验证路径 |
| unserialize | 不安全 | `unserialize`默认不限制类型 |
| display_errors | 需关闭 | 生产环境`display_errors=Off` |
| expose_php | 需关闭 | `expose_php=Off`隐藏PHP版本 |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| PHP 8.0+ | `create_function`移除 | 代码注入面减少 |
| PHP 7.4+ | `serialize`/`unserialize`安全改进 | 反序列化过滤 |
| PHP 8.1+ | Enums / Fibers | 协程支持 |
| PHP 8.2+ | `readonly`类 / DNF类型 | 不可变性支持 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——mysqli_query/PDO::query拼接 |
| vuln-patterns | VULN-INJ-CMD-01 | 命令注入——system/exec/shell_exec拼接 |
| vuln-patterns | VULN-INJ-CODE-01 | 代码注入——eval/create_function |
| vuln-patterns | VULN-INJ-DESERIAL-01 | 反序列化——unserialize不可信数据 |
| vuln-patterns | VULN-INJ-FMTSTR-01 | 格式化字符串——printf/sprintf格式参数可控 |
| vuln-patterns | VULN-FILE-TRAVERSAL-01 | 路径遍历——fopen/file_get_contents拼接 |
| vuln-patterns | VULN-FILE-SEARCHPATH-01 | LFI——include/require可控路径 |
| vuln-patterns | VULN-XSS-RAWOUTPUT-01 | 原生输出XSS——echo/print不转义 |
| vuln-patterns | VULN-ENC-ENCODING-01 | 输出编码失效——缺少htmlspecialchars |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——header('Location: ' . $url) |
| vuln-patterns | VULN-STATE-EXTCONTROL-01 | Mass assignment——直接赋值$_POST到对象 |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 信息泄露——display_errors暴露堆栈 |
| vuln-patterns | VULN-RES-COMPLEXITY-01 | ReDoS——preg_replace回溯 |
| attack-patterns | ATK-SQLI-BENIGN-01 | 良性SQL注入标记证明 |
| attack-patterns | ATK-INJ-CMD-01 | 良性命令注入标记证明 |
| attack-patterns | ATK-INJ-CODE-01 | 良性代码注入标记证明 |
| attack-patterns | ATK-INJ-DESERIAL-01 | 良性反序列化gadget证明 |
| attack-patterns | ATK-INJ-FMTSTR-01 | 良性格式化字符串证明 |
| attack-patterns | ATK-FILE-TRAVERSAL-01 | 良性路径遍历读取证明 |
| attack-patterns | ATK-FILE-SEARCHPATH-01 | 良性LFI植入证明 |
| attack-patterns | ATK-XSS-BENIGN-DOM-01 | XSS良性DOM标记证明 |
| fix-patterns | FIX-SQLI-PARAMQUERY-01 | PDO/mysqli预处理 |
| fix-patterns | FIX-INJ-CMD-01 | escapeshellarg+参数数组 |
| fix-patterns | FIX-INJ-CODE-01 | 禁用eval/create_function |
| fix-patterns | FIX-INJ-DESERIAL-01 | json_encode替代serialize |
| fix-patterns | FIX-FILE-TRAVERSAL-01 | realpath+strpos检查 |
| fix-patterns | FIX-XSS-OUTPUT-ENCODING-01 | htmlspecialchars输出编码 |
| fix-patterns | FIX-ENC-ENCODING-01 | 上下文感知编码 |

## 正例/负例

**正例**（PHP中的安全写法）：
```php
// PDO预处理
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$userId]);
$user = $stmt->fetch();

// HTML输出编码
echo htmlspecialchars($userInput, ENT_QUOTES, 'UTF-8');

// 命令执行用escapeshellarg
system('ls ' . escapeshellarg($userDir));

// 路径遍历防护
$realPath = realpath($baseDir . '/' . $filename);
if ($realPath === false || strpos($realPath, realpath($baseDir)) !== 0) {
    die('Invalid path');
}

// 输入验证
$age = filter_input(INPUT_POST, 'age', FILTER_VALIDATE_INT);
if ($age === false) die('Invalid age');
```

**负例**（PHP中的不安全写法）：
```php
// SQL拼接
mysqli_query($conn, "SELECT * FROM users WHERE name = '" . $_POST['name'] . "'");

// 命令注入
system("ls " . $_GET['dir']);

// eval
eval($_POST['code']);

// 不安全反序列化
$data = unserialize($_COOKIE['data']);

// 原生输出XSS
echo $_GET['name'];

// 文件包含
include($_GET['page'] . '.php');

// 格式化字符串
printf($_POST['format'], $data);

// 重定向无验证
header('Location: ' . $_GET['redirect']);
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用PHP技术栈
- candidate-discovery：使用PHP Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用PHP安全API/Encoder映射提供修复写法

## 官方来源

- 官方文档：https://www.php.net/docs.php
- 安全指南：https://www.php.net/manual/en/security.php
- PDO文档：https://www.php.net/manual/en/book.pdo.php
- Composer：https://getcomposer.org/

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——PHP语言生态映射 |
