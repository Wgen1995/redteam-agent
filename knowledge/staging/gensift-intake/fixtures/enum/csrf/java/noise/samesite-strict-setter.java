// 出处:人工构造(噪音:配置 setter 下发 Strict)
public class CookiePolicyApplier {
    public void apply(SessionPolicy policy, HttpServletResponse response) {
        policy.setSameSite("Strict");
        policy.applyTo(response);
    }
}
