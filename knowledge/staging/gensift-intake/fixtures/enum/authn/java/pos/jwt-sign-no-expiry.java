// 出处:人工构造(依据 CWE-613/287 签发无 setExpiration——C3 证据缺口)
public String issueAccess(Principal user) {
    return Jwts.builder().setSubject(user.getName()).signWith(key).compact();
}
