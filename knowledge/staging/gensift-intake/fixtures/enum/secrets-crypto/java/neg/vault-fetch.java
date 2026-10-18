// 出处:人工构造(硬负例:Vault 取凭据)
VaultResponse resp = vaultTemplate.read("secret/db/app");
String password = (String) resp.getData().get("password");
