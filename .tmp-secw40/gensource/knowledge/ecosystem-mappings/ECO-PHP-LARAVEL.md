# ECMAP-PHP-LARAVEL：Laravel框架生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-PHP-LARAVEL |
| name | Laravel框架生态映射 |
| version | v0.1 |
| 适用语言/框架 | PHP + Laravel Web框架 |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `artisan` CLI脚本 | Laravel标志 |
| 文件标记 | `config/app.php` / `routes/web.php` / `routes/api.php` | Laravel配置和路由 |
| 依赖标记 | `"laravel/framework"` in `composer.json` | Laravel依赖声明 |
| 框架标记 | `use Illuminate\Http\Request` / `use App\Http\Controllers\Controller` | Laravel导入签名 |
| 框架标记 | `@extends('layouts.app')` / `@yield('content')` | Blade模板标志 |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| Web路由 | `Route::get('/path', [Controller::class, 'method'])` | Web路由注册 |
| API路由 | `Route::apiResource('users', UserController::class)` | API RESTful路由 |
| 路由参数 | `Route::get('/user/{id}', ...)` | 路径参数捕获 |
| 中间件路由 | `Route::middleware(['auth'])->group(...)` | 中间件分组路由 |
| 控制器 | `class UserController extends Controller` | Laravel控制器 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| 中间件 | `php artisan make:middleware AuthMiddleware` | 自定义中间件 |
| 内置中间件 | `auth` / `verified` / `throttle` / `cors` | Laravel内置中间件 |
| 中间件组 | `protected $middlewareGroups = [...]` | 中间件组配置 |
| 全局中间件 | `$middleware` in `Kernel.php` | 全局中间件 |
| 请求验证 | `FormRequest` / `$request->validate([...])` | 请求验证 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 查询参数 | `$request->query('param')` / `$request->get('param')` | 攻击者可控 |
| 路径参数 | `public function show($id)` 从路由捕获 | 攻击者可控 |
| 请求体 | `$request->input('param')` / `$request->all()` | 攻击者可控 |
| JSON | `$request->json('param')` | 攻击者可控 |
| 请求头 | `$request->header('X-...')` | 攻击者可控 |
| Cookie | `$request->cookie('name')` | 攻击者可控 |
| 文件上传 | `$request->file('upload')` | 攻击者可控 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| Eloquent ORM | `User::where('name', $name)->first()` | 安全（参数化） |
| DB Raw | `DB::select(DB::raw("SELECT ... WHERE col = '".$val."'"))` | **危险**——SQL拼接 |
| DB Raw参数化 | `DB::select("SELECT ... WHERE col = ?", [$val])` | 安全（参数化） |
| Blade渲染 | `return view('template', ['data' => $value])` | Blade默认转义 |
| 重定向 | `return redirect($url)` | 开放重定向风险 |
| 命令执行 | `Artisan::call()` / `exec()` | 命令注入风险 |
| 文件操作 | `Storage::disk()->get($path)` | 路径遍历风险 |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| auth中间件 | `Route::middleware(['auth'])` | 要求认证 |
| Policy | `Gate::define('update-post', ...)` / `class PostPolicy` | 授权策略 |
| can指令 | `@can('update', $post)` (Blade) | Blade授权检查 |
| authorize方法 | `$this->authorize('update', $post)` | 控制器授权 |
| Sanctum | `Laravel\Sanctum` | API令牌认证 |
| Passport | `Laravel\Passport` | OAuth2 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| 表单验证 | `$request->validate([...])` / `FormRequest` | 请求验证 |
| 验证规则 | `'name' => 'required|string|max:255'` | 声明式验证规则 |
| SQL参数化 | Eloquent / `DB::select(sql, bindings)` | 参数化查询 |
| Blade转义 | `{{ $value }}` 双花括号 | Blade自动转义 |
| 文件验证 | `$request->validate(['file' => 'mimes:jpg,png|max:2048'])` | 文件类型/大小验证 |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | Blade `{{ $value }}` | 默认HTML转义 |
| HTML属性 | Blade `{{ $value }}` | 需确保引号转义 |
| JavaScript | Blade `@json($value)` / `{{ Js::from($value) }}` | JS上下文编码 |
| URL | `{{ urlencode($value) }}` | URL编码 |
| 不转义 | Blade `{!! $value !!}` | **危险**——不转义输出 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| Eloquent | `User::where('name', $name)->get()` | 参数化默认开启 |
| Eloquent whereRaw | `User::whereRaw("col = ?", [$value])` | 需参数化 |
| Query Builder | `DB::table('users')->where('name', $name)->get()` | 参数化默认开启 |
| DB::select | `DB::select("SELECT ... WHERE col = ?", [$value])` | 需手动参数化 |
| DB::raw | `DB::raw("col = '" . $value . "'")` | **危险**——SQL拼接 |
| DB::statement | `DB::statement("INSERT ... VALUES (?)", [$value])` | 需参数化 |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON | `json_encode()` / `response()->json()` | 安全 |
| Eloquent序列化 | `$model->toArray()` / `$model->toJson()` | 需`$hidden`排除敏感字段 |
| API Resource | `JsonResource` / `ResourceCollection` | 控制序列化字段 |
| PHP序列化 | `serialize()` / `unserialize()` | 不安全——避免使用 |
| XML | Laravel无内置XML解析 | XXE风险 |

## 异步与并发

| 并发模型 | 典型API | 安全注意 |
|---|---|---|
| Queue | `dispatch(new Job)` / `Queue::push()` | 异步任务队列 |
| Scheduler | `Schedule::command('task')->daily()` | 定时任务 |
| 事件 | `event(new UserCreated($user))` / `UserCreated::dispatch($user)` | 事件驱动 |
| 锁 | `Cache::lock('key', 60)` | 分布式锁 |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全注意 |
|---|---|---|
| 服务容器 | `app()->make(Service::class)` / DI注入 | Laravel IoC容器 |
| 服务提供者 | `ServiceProvider` / `register()` / `boot()` | 服务注册 |
| 依赖注入 | 构造器注入 / 方法注入 | 自动解析依赖 |
| 代码生成 | `php artisan make:*` | 代码生成命令 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 包管理 | Composer | `composer audit` |
| 测试 | PHPUnit / Pest | Laravel测试 |
| 部署 | `php artisan migrate` / `php artisan config:cache` | 部署命令 |
| 环境配置 | `.env`文件 | 生产环境APP_DEBUG=false |
| 依赖扫描 | `composer audit` / roave/security-advisories | SCA扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| Blade转义 | 开启 | `{{ }}`默认HTML转义 |
| CSRF防护 | 开启 | `VerifyCsrfToken`中间件默认启用 |
| HTTPS | 需配置 | `App::forceScheme('https')`需手动 |
| 密码哈希 | 安全 | `bcrypt()` / `Hash::make()`默认bcrypt |
| 调试模式 | 需关闭 | 生产环境`APP_DEBUG=false` |
| Mass assignment | 需fillable | `$fillable` / `$guarded`控制可赋值字段 |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Laravel 10.x | PHP 8.1+要求 | 类型安全改进 |
| Laravel 11.x | 精简目录结构 | 配置安全默认值改进 |
| Laravel 9.x | Symfony 6组件 | 安全组件更新 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-CRYPTO-NOORIGIN-01 | CSRF——`WithoutMiddleware`排除CSRF |
| vuln-patterns | VULN-XSS-AUTOESCAPE-01 | XSS——Blade `{!! !!}`不转义 |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权缺失——路由无`auth`中间件 |
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——`DB::raw`拼接 |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——`redirect($request->input('url'))` |
| vuln-patterns | VULN-STATE-EXTCONTROL-01 | Mass assignment——无`$fillable`约束 |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 信息泄露——`toArray()`含敏感字段 |
| vuln-patterns | VULN-RES-FREQUENCY-01 | 速率限制缺失——无`throttle`中间件 |
| attack-patterns | ATK-CRYPTO-CSRF-01 | CSRF良性标记证明 |
| attack-patterns | ATK-XSS-BENIGN-DOM-01 | XSS良性DOM标记证明 |
| attack-patterns | ATK-AUTHZ-DUAL-IDENTITY-01 | 双身份授权缺失证明 |
| attack-patterns | ATK-STATE-EXTCONTROL-01 | Mass assignment良性探测 |
| attack-patterns | ATK-INFO-EXPOSURE-01 | 敏感字段暴露良性探测 |
| attack-patterns | ATK-RES-FREQUENCY-01 | 速率限制缺失良性证明 |
| fix-patterns | FIX-CRYPTO-ORIGIN-01 | CSRF防护修复 |
| fix-patterns | FIX-XSS-AUTOESCAPE-01 | 恢复Blade转义 |
| fix-patterns | FIX-AUTHZ-ADDCHECK-01 | 添加auth中间件+Policy |
| fix-patterns | FIX-STATE-EXTCONTROL-01 | 设置$fillable白名单 |
| fix-patterns | FIX-INFO-EXPOSURE-01 | $hidden排除敏感字段 |

## 正例/负例

**正例**（Laravel中的安全写法）：
```php
// auth中间件 + Policy
Route::middleware(['auth'])->group(function () {
    Route::put('/posts/{post}', [PostController::class, 'update']);
});

class PostController extends Controller {
    public function update(Request $request, Post $post) {
        $this->authorize('update', $post);
        $validated = $request->validate(['title' => 'required|string|max:255']);
        $post->update($validated);
    }
}

// Eloquent参数化（默认安全）
User::where('email', $email)->first();

// $fillable约束
class User extends Model {
    protected $fillable = ['name', 'email'];
    protected $hidden = ['password', 'remember_token'];
}

// Blade转义
{{ $userInput }}

// throttle中间件
Route::post('/login', ...)->middleware('throttle:5,1');
```

**负例**（Laravel中的不安全写法）：
```php
// Blade不转义
{!! $userInput !!}

// DB::raw拼接
DB::select(DB::raw("SELECT * FROM users WHERE name = '" . $request->input('name') . "'"));

// 无$fillable约束
class User extends Model {
    // 缺少 $fillable，允许 mass assignment
}

// 重定向无验证
return redirect($request->input('redirect_url'));

// 排除CSRF
class VerifyCsrfToken extends Middleware {
    protected $except = ['*'];  // 禁用所有CSRF检查
}

// 无auth中间件
Route::delete('/users/{id}', [UserController::class, 'destroy']);
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Laravel框架
- candidate-discovery：使用Laravel Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用Laravel安全API/中间件配置提供修复写法

## 官方来源

- 官方文档：https://laravel.com/docs/
- 安全指南：https://laravel.com/docs/security
- Eloquent ORM：https://laravel.com/docs/eloquent
- Blade模板：https://laravel.com/docs/blade

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Laravel框架生态映射 |
