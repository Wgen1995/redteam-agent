package com.acme.svc;

import javax.xml.parsers.DocumentBuilderFactory;

public class UserService {
    private final TokenStore tokens;

    public UserService(TokenStore tokens) {
        this.tokens = tokens;
    }

    public boolean resetPassword(String token) {
        String user = tokens.consume(token);
        return user != null;
    }

    public Object parseProfile(String xml) throws Exception {
        Object builder = DocumentBuilderFactory.newInstance().newDocumentBuilder();
        return builder;
    }

    public Object findUser(String name) throws Exception {
        Object stmt = tokens.statement();
        Object rows = stmt.executeQuery("SELECT * FROM users WHERE n = '" + name + "'");
        return rows;
    }
}
