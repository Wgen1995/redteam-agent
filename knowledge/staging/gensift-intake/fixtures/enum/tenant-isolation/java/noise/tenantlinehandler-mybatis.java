// 出处:人工构造(噪音:租户行级插件完整覆盖——锚在,由五步判别,符合 INV-005)
@Configuration
public class TenantConfig {
    @Bean
    public MybatisPlusInterceptor interceptor(TenantLineHandler handler) {
        MybatisPlusInterceptor i = new MybatisPlusInterceptor();
        i.addInnerInterceptor(new TenantLineInnerInterceptor(handler)); // 全部 ORM 通道被重写
        return i;
    }
}
