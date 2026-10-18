// 出处:人工构造(噪音:登录后新建会话——轮换修复形态)
@Bean
SecurityFilterChain chain(HttpSecurity http) throws Exception {
    http.formLogin(Customizer.withDefaults())
        .sessionManagement(s -> s.sessionFixation().newSession());
    return http.build();
}
