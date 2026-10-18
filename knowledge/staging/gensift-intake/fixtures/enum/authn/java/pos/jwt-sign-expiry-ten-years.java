// 出处:人工构造(依据 CWE-613 超长有效期签发)
public String issueAccess(Principal user) {
    return Jwts.builder().setSubject(user.getName())
        .setExpiration(Date.from(Instant.now().plus(3650, ChronoUnit.DAYS)))
        .signWith(key)
        .compact();
}
