// 出处:人工构造(硬负例:仅校验 scheme 前缀,无外发)
if (!imageUrl.startsWith("https://")) {
    throw new BadRequestException("scheme must be https");
}
return imageUrl;
