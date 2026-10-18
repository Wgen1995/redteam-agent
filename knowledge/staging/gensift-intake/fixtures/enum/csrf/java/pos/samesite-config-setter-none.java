// 出处:人工构造(依据 CWE-352 自定义配置 setter 下发 None 形态)
public class CookiePolicyApplier {
    public void apply(SessionPolicy policy, HttpServletResponse response) {
        policy.setSameSite("None");
        policy.applyTo(response);
    }
}
