// 出处:人工构造(硬负例:摘要计算)
byte[] mac = Mac.getInstance("HmacSHA256").doFinal(body);
