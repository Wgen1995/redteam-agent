// 出处:人工构造(噪音:cookie 仓库默认 HttpOnly 形态+Strict 会话)
@Bean
SecurityFilterChain chain(HttpSecurity http) throws Exception {
    http.csrf(c -> c.csrfTokenRepository(new CookieCsrfTokenRepository()));
    return http.build();
}
