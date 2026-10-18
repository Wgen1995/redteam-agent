// 出处:人工构造(噪音:持久化 token 仓库+安全 cookie 的 remember-me)
@Bean
SecurityFilterChain chain(HttpSecurity http) throws Exception {
    http.rememberMe(r -> r.tokenRepository(persistentTokenRepository).useSecureCookie(true).tokenValiditySeconds(86400));
    return http.build();
}
