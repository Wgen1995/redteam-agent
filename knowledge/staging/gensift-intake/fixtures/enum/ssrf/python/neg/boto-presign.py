# 出处:人工构造(硬负例:生成预签名 URL,无外发)
url = s3.generate_presigned_url("get_object", Params={"Bucket": b, "Key": k}, ExpiresIn=300)
return url
