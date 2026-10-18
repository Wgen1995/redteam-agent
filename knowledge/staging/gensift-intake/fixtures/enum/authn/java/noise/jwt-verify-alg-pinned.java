// 出处:人工构造(噪音:钉死算法族的验签)
public DecodedJWT check(String token) {
    return JWT.require(Algorithm.RSA256(publicKey, null)).build().verify(token);
}
