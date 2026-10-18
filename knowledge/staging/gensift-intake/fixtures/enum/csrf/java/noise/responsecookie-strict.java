// 出处:人工构造(噪音:SameSite=Strict+Secure+HttpOnly 全属性下发)
public ResponseCookie sessionCookie(String value) {
    return ResponseCookie.from("sid", value)
        .httpOnly(true).secure(true).path("/").sameSite("Strict")
        .maxAge(Duration.ofHours(8))
        .build();
}
