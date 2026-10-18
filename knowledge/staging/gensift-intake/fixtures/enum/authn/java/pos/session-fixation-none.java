// 出处:人工构造(依据 CWE-384 显式关闭登录后轮换)
@Bean
SecurityFilterChain chain(HttpSecurity http) throws Exception {
    http.formLogin(Customizer.withDefaults())
        .sessionManagement(s -> s.sessionFixation().none());
    return http.build();
}
