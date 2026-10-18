// 出处:人工构造(依据 CWE-639 Spring Data 旧式 getById 形态)
@GetMapping("/accounts/{accountId}/balance")
public BigDecimal balance(@PathVariable Long accountId) {
    Account account = accountRepository.getById(accountId);
    return account.getBalance();
}
