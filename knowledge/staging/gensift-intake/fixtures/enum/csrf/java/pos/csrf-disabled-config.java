// 出处:人工构造(依据 CWE-352 Spring Security 显式关闭 CSRF——REST 豁免高频形态)
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    SecurityFilterChain chain(HttpSecurity http) throws Exception {
        http.csrf().disable().authorizeHttpRequests(a -> a.anyRequest().authenticated());
        return http.build();
    }
}
