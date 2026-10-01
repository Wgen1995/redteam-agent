# ECMAP-CPP：C/C++语言生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-CPP |
| name | C/C++语言生态映射 |
| version | v0.1 |
| 适用语言/框架 | C / C++（原生编译，无GC，手动内存管理） |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `CMakeLists.txt` / `Makefile` / `configure.ac` | C/C++构建文件 |
| 文件标记 | `.c` / `.cpp` / `.cc` / `.cxx` / `.h` / `.hpp` 源文件 | C/C++源码标识 |
| 文件标记 | `.so` / `.dll` / `.a` / `.dylib` 库文件 | 编译产物 |
| 依赖标记 | `#include <stdio.h>` (C) / `#include <iostream>` (C++) | 标准库头文件 |
| 框架标记 | Qt / Boost / OpenSSL 依赖 | 第三方库 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| main函数 | `int main(int argc, char *argv[])` | C/C++程序入口 |
| WinMain | `int WINAPI WinMain(...)` | Windows GUI入口 |
| 信号处理 | `signal(SIGTERM, handler)` | 信号回调 |
| 线程入口 | `pthread_create(&t, NULL, func, arg)` / `std::thread` | 线程入口 |
| 回调注册 | `register_callback(handler)` | 回调函数注册 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| 信号处理 | `sigaction` / `signal` | 信号中断处理 |
| 错误处理 | `setjmp`/`longjmp` (C) / `try-catch` (C++) | 异常/错误处理 |
| RAII | 构造函数获取/析构函数释放 | 资源管理（C++） |
| 智能指针 | `std::unique_ptr` / `std::shared_ptr` | 自动内存管理（C++） |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 命令行参数 | `argv[i]` / `argc` | 攻击者可控 |
| 环境变量 | `getenv("VAR")` | 部分可控 |
| 文件输入 | `fread()` / `read()` / `fscanf()` | 攻击者可控（文件内容） |
| 网络输入 | `recv()` / `read()` on socket / `recvfrom()` | 攻击者可控 |
| stdin | `scanf()` / `fgets(stdin)` / `std::cin` | 攻击者可控 |
| IOCTL | `ioctl(fd, cmd, data)` | 攻击者可控（内核场景） |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| 内存拷贝 | `memcpy()` / `strcpy()` / `strcat()` / `sprintf()` | 缓冲区溢出风险 |
| 命令执行 | `system()` / `popen()` / `exec*()` | 命令注入风险 |
| 文件操作 | `fopen()` / `open()` / `fopen_s()` | 路径遍历风险 |
| 指针解引用 | `*ptr` / `ptr->field` | 空指针/野指针风险 |
| 格式化 | `printf()` / `sprintf()` / `fprintf()` / `syslog()` | 格式化字符串风险 |
| 动态内存 | `malloc()` / `free()` / `new` / `delete` | 内存泄漏/UAF风险 |
| 网络 | `send()` / `connect()` | SSRF/信息泄露风险 |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| 权限检查 | `getuid()` / `access()` | 系统级权限检查 |
| 边界检查 | `if (len < buf_size)` | 手动边界检查 |
| 输入验证 | 手动验证函数 | 无标准框架——需手动实现 |
| SELinux | SELinux上下文检查 | 强制访问控制 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 边界检查 | `strncpy()` / `strncat()` / `snprintf()` | 长度限制版本 |
| 安全函数 | `strcpy_s()` / `strcat_s()` (C11 Annex K) | 安全替代函数 |
| 输入验证 | 手动检查 | 无标准框架 |
| 路径净化 | `realpath()` + `strncmp()` | 规范化+前缀验证 |
| 整数溢出检查 | `__builtin_add_overflow()` (GCC/Clang) | 编译器内置溢出检查 |
| ASan | `-fsanitize=address` | 地址消毒器（测试用） |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML | 无内置——需第三方库 | 手动HTML编码 |
| URL | 无内置——需手动实现 | 手动URL编码 |
| 日志 | `syslog()` / `fprintf(stderr, ...)` | 格式化字符串风险 |
| 输出 | `printf()` / `puts()` / `fputs()` | 格式化字符串风险 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| 原生SQL | `mysql_query()` / `sqlite3_exec()` / `PQexec()` | 需参数化（预处理语句） |
| 预处理 | `mysql_stmt_prepare()` / `sqlite3_prepare_v2()` / `PQprepare()` | 参数化查询 |
| 字符串拼接 | `sprintf(sql, "SELECT ... WHERE col = '%s'", val)` | **危险**——SQL注入 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| 二进制 | `memcpy(&struct, buffer, sizeof(struct))` | 内存布局依赖——结构体对齐/大小端 |
| JSON | `jansson` / `nlohmann/json` / `rapidjson` | 安全（无代码执行） |
| XML | `libxml2` / `expat` / `tinyxml` | XXE风险——需禁用外部实体 |
| CSV | 手动解析 / `libcsv` | CSV公式注入风险 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| pthread | `pthread_create()` / `pthread_mutex_lock()` | POSIX线程 |
| std::thread | `std::thread` / `std::mutex` / `std::lock_guard` | C++线程（RAII锁） |
| 原子操作 | `std::atomic<T>` / `_Atomic` | 原子操作 |
| async | `std::async()` / `std::future` | 异步任务 |
| 信号量 | `sem_wait()` / `sem_post()` | POSIX信号量 |
| 条件变量 | `pthread_cond_wait()` / `std::condition_variable` | 条件变量 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 函数指针 | `void (*func)(int)` | 函数指针——来自外部需白名单 |
| dlopen/dlsym | `dlopen(lib)` / `dlsym(handle, name)` | 动态库加载——路径/符号来自外部需验证 |
| RTTI | `dynamic_cast` / `typeid` (C++) | 运行时类型信息 |
| 模板元编程 | C++模板 | 编译时代码生成 |
| 宏 | `#define` / `#ifdef` | 预处理宏——注意副作用 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 构建工具 | CMake / Make / Ninja / Bazel | 构建配置安全 |
| 包管理 | vcpkg / Conan / apt / yum | 依赖安全 |
| 编译选项 | `-fstack-protector` / `-D_FORTIFY_SOURCE` / `-fPIE` | 安全编译选项 |
| 测试框架 | Google Test / Catch2 / Unity | 测试集成 |
| 静态分析 | Clang Static Analyzer / CPPcheck / CodeQL | 安全分析 |
| 消毒器 | ASan / UBSan / TSan / MSan | 运行时安全检测 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| 边界检查 | 不安全 | `memcpy`/`strcpy`不检查边界 |
| 内存安全 | 不安全 | 手动内存管理——UAF/溢出/泄漏 |
| 类型安全 | 部分 | C弱类型，C++较强但仍可绕过 |
| 整数溢出 | 不安全 | 有符号整数溢出为UB |
| 栈保护 | 需启用 | `-fstack-protector`需编译时启用 |
| ASLR/PIE | 需启用 | `-fPIE`需编译时启用 |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| C11 Annex K | `*_s`安全函数（可选） | 边界检查函数 |
| C++17 | `std::optional` / `std::variant` | 更安全的类型 |
| C++20 | `std::span` / concepts / ranges | 更安全的容器访问 |
| C++23 | `std::expected` / `std::print` | 错误处理改进 |
| GCC/Clang | `-fsanitize=address`等 | 运行时安全检测 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-MEM-BOUNDS-01 | 缓冲区溢出——memcpy/strcpy无边界检查 |
| vuln-patterns | VULN-MEM-INDEX-01 | 越界索引——数组下标未检查 |
| vuln-patterns | VULN-MEM-LAYOUT-01 | 内存布局依赖——memcpy结构体 |
| vuln-patterns | VULN-MEM-NULLTERM-01 | 空终止符缺失——strncpy未设\0 |
| vuln-patterns | VULN-MEM-PTR-01 | 不可信指针——IOCTL指针字段解引用 |
| vuln-patterns | VULN-CODE-DANGEROUS-01 | 危险函数——gets/strcpy/sprintf |
| vuln-patterns | VULN-CODE-UNDEF-01 | 未定义行为——整数溢出/未初始化 |
| vuln-patterns | VULN-INJ-CMD-01 | 命令注入——system拼接 |
| vuln-patterns | VULN-INJ-FMTSTR-01 | 格式化字符串——printf格式参数可控 |
| vuln-patterns | VULN-FILE-TRAVERSAL-01 | 路径遍历——fopen拼接 |
| vuln-patterns | VULN-RES-UAF-01 | 释放后使用——free后使用 |
| vuln-patterns | VULN-RES-INIT-01 | 未初始化使用——malloc后未清零 |
| vuln-patterns | VULN-RES-REFCOUNT-01 | 引用计数错误——retain/release不配对 |
| vuln-patterns | VULN-TYPE-CAST-01 | 类型转换错误——有符号到无符号转换 |
| vuln-patterns | VULN-CALC-INTOVERFLOW-01 | 整数溢出——malloc(len*sizeof)无检查 |
| vuln-patterns | VULN-CONC-RACE-01 | TOCTOU——检查与使用间无原子性 |
| attack-patterns | ATK-MEM-BOUNDS-01 | 缓冲区溢出良性标记证明（ASan） |
| attack-patterns | ATK-MEM-INDEX-01 | 越界索引良性标记证明（ASan） |
| attack-patterns | ATK-MEM-LAYOUT-01 | 布局差异良性证明 |
| attack-patterns | ATK-MEM-NULLTERM-01 | 空终止符过读良性证明（ASan） |
| attack-patterns | ATK-MEM-PTR-01 | 不可信指针良性证明（NULL触发） |
| attack-patterns | ATK-CODE-DANGEROUS-01 | 危险函数良性探测 |
| attack-patterns | ATK-CODE-UNDEF-01 | UB良性探测（UBSan） |
| attack-patterns | ATK-INJ-CMD-01 | 命令注入良性标记证明 |
| attack-patterns | ATK-INJ-FMTSTR-01 | 格式化字符串良性证明 |
| attack-patterns | ATK-RES-UAF-01 | UAF良性悬垂引用证明 |
| fix-patterns | FIX-MEM-BOUNDS-01 | 边界检查+安全函数 |
| fix-patterns | FIX-MEM-INDEX-01 | 索引范围检查 |
| fix-patterns | FIX-MEM-LAYOUT-01 | 显式序列化替代memcpy |
| fix-patterns | FIX-MEM-NULLTERM-01 | 确保空终止符 |
| fix-patterns | FIX-CODE-DANGEROUS-01 | 安全函数替代 |
| fix-patterns | FIX-CODE-UNDEF-01 | 消除UB |
| fix-patterns | FIX-INJ-FMTSTR-01 | 固定格式字符串 |
| fix-patterns | FIX-RES-UAF-01 | 智能指针/置NULL |
| fix-patterns | FIX-RES-INIT-01 | 初始化所有变量 |
| fix-patterns | FIX-TYPE-CAST-01 | 安全转换检查 |

## 正例/负例

**正例**（C/C++中的安全写法）：
```c
// 边界检查拷贝
strncpy(dst, src, dst_size - 1);
dst[dst_size - 1] = '\0';

// snprintf替代sprintf
snprintf(buf, sizeof(buf), "SELECT * FROM users WHERE id = %d", id);

// 智能指针（C++）
auto ptr = std::make_unique<Resource>();
// 自动释放，无需手动delete

// RAII锁（C++）
std::lock_guard<std::mutex> lock(mu);
// 自动释放，无需手动unlock

// 溢出检查
size_t total;
if (__builtin_mul_overflow(count, sizeof(Item), &total)) {
    return ERROR;  // 溢出
}
void *buf = malloc(total);

// 格式化字符串固定
printf("%s", user_input);  // 而非 printf(user_input)
```

**负例**（C/C++中的不安全写法）：
```c
// 缓冲区溢出
strcpy(dst, src);  // 无长度限制
memcpy(dst, src, len);  // len来自源而非目标大小

// sprintf溢出
sprintf(buf, "SELECT * FROM users WHERE name = '%s'", name);

// 格式化字符串
printf(user_input);  // 格式参数可控

// 释放后使用
free(ptr);
ptr->field = value;  // UAF

// 未初始化使用
int *p = (int *)malloc(sizeof(int));
if (*p > 0) { ... }  // 未初始化读取

// 命令注入
system("ls " + user_dir);

// 整数溢出
void *buf = malloc(count * sizeof(Item));  // 无溢出检查
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用C/C++技术栈
- candidate-discovery：使用C/C++ Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用C/C++安全函数/编译选项映射提供修复写法

## 官方来源

- CERT C：https://www.securecoding.cert.org/confluence/display/c/SEI+CERT+C+Coding+Standard
- CERT C++：https://www.securecoding.cert.org/confluence/pages/viewpage.action?pageId=637
- Clang sanitizer：https://clang.llvm.org/docs/AddressSanitizer.html
- OWASP C/C++：https://owasp.org/www-community/controls/Static_Code_Analysis

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——C/C++语言生态映射 |
