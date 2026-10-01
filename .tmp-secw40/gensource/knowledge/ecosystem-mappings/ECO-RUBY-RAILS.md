# ECMAP-RUBY-RAILS：Ruby/Rails生态映射

> **生态映射条目，经人工复核后纳入正式知识。**

## 元数据

| 字段 | 值 |
|---|---|
| stable_id | ECMAP-RUBY-RAILS |
| name | Ruby/Rails生态映射 |
| version | v0.1 |
| 适用语言/框架 | Ruby + Ruby on Rails Web框架 |
| 消费方 | scope-and-context, candidate-discovery, remediation-guidance |

## 识别信号（文件/依赖/框架标记）

| 信号类型 | 信号模式 | 说明 |
|---|---|---|
| 文件标记 | `Gemfile` / `Gemfile.lock` | Ruby项目依赖文件 |
| 文件标记 | `.rb`源文件 | Ruby源码标识 |
| 文件标记 | `config/routes.rb` / `config/application.rb` | Rails配置文件 |
| 框架标记 | `Rails.application.routes.draw do` | Rails路由配置标志 |
| 框架标记 | `ApplicationController < ActionController::Base` | Rails控制器标志 |
| 框架标记 | `ActiveRecord::Base` 子类 | Rails模型标志 |
| 运行时标记 | `Rakefile` / `bin/rails` | Rails CLI |

## 入口注册

| 注册方式 | 典型写法 | 说明 |
|---|---|---|
| 资源路由 | `resources :users` in `routes.rb` | RESTful资源路由 |
| 自定义路由 | `get '/path', to: 'controller#action'` | 自定义路由 |
| 路径参数 | `get '/users/:id', to: 'users#show'` | 路径参数捕获 |
| 命名空间 | `namespace :api do resources :users end` | 命名空间路由 |
| concerns | `concern :commentable do ... end` | 可复用路由模块 |

## 中间件、过滤器与拦截器

| 组件类型 | 典型写法 | 安全相关注意 |
|---|---|---|
| before_action | `before_action :authenticate_user!` | 控制器前置过滤器 |
| after_action | `after_action :set_headers` | 控制器后置过滤器 |
| around_action | `around_action :wrap_in_transaction` | 环绕过滤器 |
| Rack中间件 | `config.middleware.use MyMiddleware` | Rack中间件 |
| 异常处理 | `rescue_from` | 控制器异常捕获 |

## Source API

| API类型 | 典型API | 攻击者可控性 |
|---|---|---|
| 查询参数 | `params[:param]` / `params[:id]` | 攻击者可控 |
| 路径参数 | `params[:id]` 从路由捕获 | 攻击者可控 |
| 请求体 | `params[:user][:name]`（嵌套参数） | 攻击者可控 |
| 请求头 | `request.headers['X-...']` | 攻击者可控 |
| Cookie | `cookies[:name]` / `request.cookies` | 攻击者可控 |
| 文件上传 | `params[:file]` / `ActionDispatch::Http::UploadedFile` | 攻击者可控 |
| Session | `session[:user_id]` | 服务端存储 |

## Sink API

| API类型 | 典型API | 危险性 |
|---|---|---|
| ActiveRecord查询 | `User.where(name: name)` | 安全（参数化） |
| Raw SQL | `User.where("name = '#{name}'")` | **危险**——SQL注入 |
| 参数化SQL | `User.where("name = ?", name)` | 安全（参数化） |
| ERB渲染 | `render template: 'page'` / `<%= @value %>` | ERB默认转义 |
| 重定向 | `redirect_to url` | 开放重定向风险 |
| 命令执行 | `system(cmd)` / `exec(cmd)` / backticks `` `cmd` `` | 命令注入风险 |
| 文件操作 | `File.read(path)` / `File.join(dir, name)` | 路径遍历风险 |
| 反序列化 | `Marshal.load()` / `YAML.load()` | 反序列化RCE风险 |
| 模板 | `.erb` / `.haml` / `.slim` | XSS风险（需转义） |

## Guard与授权框架

| 框架组件 | 典型写法 | 说明 |
|---|---|---|
| Devise | `before_action :authenticate_user!` | Devise认证 |
| Pundit | `authorize @user` / `class UserPolicy` | Pundit授权 |
| CanCanCan | `can? :update, @user` / `class Ability` | CanCanCan授权 |
| before_action | `before_action :require_login` | 自定义鉴权 |
| current_user | `current_user` (Devise) | 当前用户代理 |
| CSRF | `protect_from_forgery` | Rails内置CSRF防护 |

## Sanitizer

| 净化类型 | 典型API | 说明 |
|---|---|---|
| Strong Parameters | `params.require(:user).permit(:name, :email)` | Mass assignment防护 |
| 验证 | `validates :name, presence: true, length: { maximum: 100 }` | 模型验证 |
| SQL参数化 | `where("col = ?", value)` / `where(col: value)` | 参数化查询 |
| HTML净化 | `sanitize()` / `Rails::Html::SafeListSanitizer` | Rails内置HTML净化 |
| ERB转义 | `<%= value %>` / `html_escape()` | ERB默认转义 |
| 路径净化 | `File.expand_path()` + `start_with?()` | 路径规范化 |

## Encoder与输出上下文

| 输出上下文 | 典型API | 说明 |
|---|---|---|
| HTML body | ERB `<%= value %>` 自动转义 | ERB默认HTML转义 |
| HTML属性 | ERB自动转义 | 需确保引号转义 |
| JavaScript | `j()` / `escape_javascript()` | JS上下文转义 |
| URL | `url_for()` / `CGI.escape()` | URL编码 |
| 不转义 | `<%= raw value %>` / `<%== value %>` | **危险**——不转义输出 |
| html_safe | `value.html_safe` | **危险**——标记为安全跳过转义 |

## ORM与Raw API

| API类型 | 典型API | 安全注意 |
|---|---|---|
| ActiveRecord | `User.where(name: name)` / `User.find(id)` | 参数化默认开启——安全 |
| where条件 | `User.where("name = ?", name)` | 参数化——安全 |
| where拼接 | `User.where("name = '#{name}'")` | **危险**——SQL注入 |
| order拼接 | `User.order("#{params[:sort]}")` | **危险**——SQL注入 |
| find_by_sql | `User.find_by_sql(["SELECT ... WHERE col = ?", value])` | 需参数化 |
| Arel | `User.where(User.arel_table[:name].eq(name))` | 安全——Arel AST |

## 序列化与解析

| 操作类型 | 典型API | 安全注意 |
|---|---|---|
| JSON | `as_json` / `to_json` / `ActiveModel::Serializer` | 需控制字段 |
| Marshal | `Marshal.load()` / `Marshal.dump()` | **不安全**——RCE风险 |
| YAML | `YAML.safe_load()` vs `YAML.load()` | `safe_load`限制类型——安全 |
| XML | `Nokogiri::XML` / `ActiveSupport::XmlMini` | XXE风险——需配置 |
| CSV | `CSV.parse()` / `CSV.read()` | CSV公式注入风险 |

## 异步与并发

| 并发模型 | 典型API | 安全相关注意 |
|---|---|---|
| Sidekiq | `SomeJob.perform_async(args)` | 后台任务队列 |
| ActiveJob | `SomeJob.set(wait: 5.minutes).perform_later` | Rails ActiveJob |
| Threads | `Thread.new { ... }` | Ruby线程（GIL限制） |
| Mutex | `Mutex.new.synchronize { ... }` | 互斥锁 |
| Async | `async` gem / `Fibers` | 异步编程 |
| Ractors | `Ractor.new { ... }` (Ruby 3.0+) | 并行执行（无GIL） |

## 反射、DI与代码生成

| 机制类型 | 典型API | 安全相关注意 |
|---|---|---|
| send | `obj.send(method_name, args)` | 方法名来自外部需白名单 |
| public_send | `obj.public_send(method_name, args)` | 仅公开方法——更安全 |
| const_get | `Object.const_get(class_name)` | 类名来自外部需白名单 |
| eval | `eval(string)` | **危险**——代码注入 |
| instance_variable_get/set | `obj.instance_variable_get(:@var)` | 实例变量动态访问 |
| method_missing | `method_missing` | 动态方法——需注意安全 |
| 依赖注入 | Rails无内置DI容器 | 通常通过Service Object模式 |

## 构建、包管理与测试

| 维度 | 典型工具/配置 | 安全注意 |
|---|---|---|
| 包管理 | Bundler (`Gemfile`) | 依赖安全——`bundle audit` |
| 构建 | `rails assets:precompile` | 资源编译 |
| 测试 | RSpec / Minitest / Capybara | Rails测试 |
| 静态分析 | Brakeman / RuboCop | Brakeman安全专项扫描 |
| 依赖扫描 | `bundle audit` / `bundler-audit` | SCA扫描 |

## 默认安全行为

| 行为 | 默认状态 | 说明 |
|---|---|---|
| ERB转义 | 开启 | Rails 3+ ERB默认HTML转义 |
| CSRF防护 | 开启 | `protect_from_forgery`默认启用 |
| Strong Parameters | 需使用 | Rails 4+需显式`permit` |
| 密码哈希 | 安全 | `has_secure_password`用bcrypt |
| Session安全 | 可配置 | `config.force_ssl` / cookie settings |
| YAML | `safe_load`推荐 | `YAML.load`在Ruby 3.0+默认安全 |
| 错误页面 | 需配置 | 生产环境`config.consider_all_requests_local = false` |

## 版本变化

| 版本 | 安全相关变化 | 影响 |
|---|---|---|
| Rails 7.x | `YAML.safe_load`默认 | YAML安全 |
| Rails 6.1+ | `strict_loading` | 防止N+1和意外加载 |
| Ruby 3.0+ | `YAML.load`默认safe_load行为 | YAML安全改进 |
| Ruby 3.0+ | Ractors | 并行安全 |
| Rails 7.1+ | `authenticate_by` | 更安全的认证方法 |

## 漏洞/攻击/修复模式引用

| 知识库 | 条目ID | 说明 |
|---|---|---|
| vuln-patterns | VULN-SQLI-STRCONCAT-01 | SQL注入——where/order拼接 |
| vuln-patterns | VULN-INJ-CMD-01 | 命令注入——system/exec/backticks拼接 |
| vuln-patterns | VULN-INJ-CODE-01 | 代码注入——eval/send可控 |
| vuln-patterns | VULN-INJ-DESERIAL-01 | 反序列化——Marshal.load/YAML.load |
| vuln-patterns | VULN-FILE-TRAVERSAL-01 | 路径遍历——File.read拼接 |
| vuln-patterns | VULN-XSS-AUTOESCAPE-01 | XSS——raw/html_safe不转义 |
| vuln-patterns | VULN-CRYPTO-NOORIGIN-01 | CSRF——protect_from_forgery禁用 |
| vuln-patterns | VULN-AUTHZ-MISSING-01 | 授权缺失——无before_action鉴权 |
| vuln-patterns | VULN-STATE-EXTCONTROL-01 | Mass assignment——无strong parameters |
| vuln-patterns | VULN-CFLOW-OPENREDIRECT-01 | 开放重定向——redirect_to可控 |
| vuln-patterns | VULN-INFO-EXPOSURE-01 | 信息泄露——as_json含敏感字段 |
| vuln-patterns | VULN-RES-FREQUENCY-01 | 速率限制缺失——无rack-attack |
| attack-patterns | ATK-SQLI-BENIGN-01 | 良性SQL注入标记证明 |
| attack-patterns | ATK-INJ-CMD-01 | 良性命令注入标记证明 |
| attack-patterns | ATK-INJ-CODE-01 | 良性代码注入标记证明 |
| attack-patterns | ATK-INJ-DESERIAL-01 | 良性反序列化gadget证明 |
| attack-patterns | ATK-CRYPTO-CSRF-01 | CSRF良性标记证明 |
| attack-patterns | ATK-XSS-BENIGN-DOM-01 | XSS良性DOM标记证明 |
| attack-patterns | ATK-AUTHZ-DUAL-IDENTITY-01 | 双身份授权缺失证明 |
| attack-patterns | ATK-STATE-EXTCONTROL-01 | Mass assignment良性探测 |
| fix-patterns | FIX-SQLI-PARAMQUERY-01 | where参数化 |
| fix-patterns | FIX-INJ-CMD-01 | 参数数组替代shell |
| fix-patterns | FIX-XSS-AUTOESCAPE-01 | 移除raw/html_safe |
| fix-patterns | FIX-CRYPTO-ORIGIN-01 | 恢复CSRF防护 |
| fix-patterns | FIX-AUTHZ-ADDCHECK-01 | before_action+Pundit |
| fix-patterns | FIX-STATE-EXTCONTROL-01 | Strong Parameters permit |

## 正例/负例

**正例**（Ruby/Rails中的安全写法）：
```ruby
# Strong Parameters
def user_params
  params.require(:user).permit(:name, :email, :password)
end

# ActiveRecord参数化（默认安全）
User.where(name: params[:name])
User.where("name = ?", params[:name])

# before_action鉴权
class UsersController < ApplicationController
  before_action :authenticate_user!
  before_action -> { authorize @user }, only: [:update, :destroy]

  def destroy
    @user = User.find(params[:id])
    @user.destroy
    redirect_to users_path
  end
end

# ERB转义
<%= @user_input %>  <!-- 自动HTML转义 -->

# YAML.safe_load
config = YAML.safe_load(yaml_string, permitted_classes: [Symbol])
```

**负例**（Ruby/Rails中的不安全写法）：
```ruby
# SQL拼接
User.where("name = '#{params[:name]}'")
User.order("#{params[:sort]} DESC")

# 命令注入
system("ls #{params[:dir]}")
`ls #{params[:dir]}`

# eval
eval(params[:expression])

# raw/html_safe
<%= raw @user_input %>
@content.html_safe

# Marshal.load
data = Marshal.load(user_data)

# 无strong parameters
User.create(params[:user])  # 允许所有字段（包括is_admin）

# 重定向无验证
redirect_to params[:return_url]

# 无鉴权
class UsersController < ApplicationController
  def destroy
    User.find(params[:id]).destroy  # 无before_action
  end
end
```

## 消费Skill

- scope-and-context：消费识别信号判断目标使用Ruby/Rails技术栈
- candidate-discovery：使用Rails Source/Sink API映射辅助模式驱动发现
- remediation-guidance：使用Rails安全API/配置提供修复写法

## 官方来源

- 官方文档：https://guides.rubyonrails.org/
- 安全指南：https://guides.rubyonrails.org/security.html
- Brakeman：https://brakemanscanner.org/
- bundler-audit：https://github.com/rubysec/bundler-audit

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-08-09 | KBATCH-006：初始创建——Ruby/Rails生态映射 |
