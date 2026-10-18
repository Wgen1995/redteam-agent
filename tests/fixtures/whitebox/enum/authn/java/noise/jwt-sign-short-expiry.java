// 出处:人工构造(噪音:短有效期签发)
public String issueAccess(Principal user) {
    return Jwts.builder().setSubject(user.getName())
        .setExpiration(Date.from(Instant.now().plus(15, ChronoUnit.MINUTES)))
        .signWith(key)
        .compact();
}
