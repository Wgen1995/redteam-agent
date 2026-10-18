// 出处:人工构造(硬负例:正则格式校验)
boolean wellFormed = Pattern.matches("^[^@\\s]+@[^@\\s]+\\.[a-z]{2,}$", email);
