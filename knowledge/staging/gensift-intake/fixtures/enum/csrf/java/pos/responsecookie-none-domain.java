// 出处:人工构造(依据 CWE-352 ResponseCookie SameSite=None+宽 Domain 形态)
public ResponseCookie sessionCookie(String value) {
    return ResponseCookie.from("sid", value)
        .path("/")
        .domain(".shop-parent.com")
        .sameSite("None")
        .maxAge(Duration.ofHours(8))
        .build();
}
