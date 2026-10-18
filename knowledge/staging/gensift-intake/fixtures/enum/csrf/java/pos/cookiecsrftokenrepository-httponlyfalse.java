// 出处:人工构造(依据 CWE-352 SPA 双提交 cookie 仓库,C-g 子域种入面向)
@Bean
SecurityFilterChain spaChain(HttpSecurity http) throws Exception {
    http.csrf(c -> c.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse()));
    return http.build();
}
