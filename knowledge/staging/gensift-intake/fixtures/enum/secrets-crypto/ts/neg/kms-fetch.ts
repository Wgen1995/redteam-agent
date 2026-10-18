// 出处:人工构造(硬负例:KMS/Secrets Manager 取值)
const { SecretString } = await client.send(new GetSecretValueCommand({ SecretId: "prod/db" }));
