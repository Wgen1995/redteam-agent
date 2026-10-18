// 出处:人工构造(硬负例:正则校验)
public boolean validRecipient(String email) {
    return Pattern.compile("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$").matcher(email).matches();
}
