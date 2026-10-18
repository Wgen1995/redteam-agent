// 出处:人工构造(依据 CWE-287 remember-me 弱密钥+超长有效期)
@Bean
SecurityFilterChain chain(HttpSecurity http) throws Exception {
    http.rememberMe(r -> r.key("changeme").tokenValiditySeconds(31536000));
    return http.build();
}
