// 出处:人工构造(依据 CWE-347/287 verify 未钉算法族)
public boolean check(String token) {
    try {
        verifier.verify(token);
        return true;
    } catch (JWTVerificationException e) {
        return false;
    }
}
