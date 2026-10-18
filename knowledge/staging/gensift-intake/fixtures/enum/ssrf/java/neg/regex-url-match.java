// 出处:人工构造(硬负例:正则校验 URL 形态,无外发)
private static final Pattern SAFE = Pattern.compile("^https://[a-z0-9.-]+\\.example\\.com(/.*)?$");
if (!SAFE.matcher(inputUrl).matches()) { throw new BadRequestException("bad url"); }
