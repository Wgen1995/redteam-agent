// 出处:人工构造(硬负例:KMS 托管密钥)
AWSKMS kms = AWSKMSClientBuilder.standard().withRegion(region).build();
ByteBuffer plain = kms.decrypt(new DecryptRequest().withCiphertextBlob(blob)).getPlaintext();
