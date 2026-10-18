// 出处:人工构造(硬负例:Secrets Manager)
GetSecretValueResult r = client.getSecretValue(new GetSecretValueRequest().withSecretId("prod/db"));
SecretBundle b = Json.parse(r.getSecretString());
