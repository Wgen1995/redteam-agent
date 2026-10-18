// 出处:人工构造(硬负例:Jakarta Validation 注解声明式)
public class SignupForm {
    @NotBlank @Email
    private String email;
    @Size(min = 8, max = 64)
    private String passphrase;
}
