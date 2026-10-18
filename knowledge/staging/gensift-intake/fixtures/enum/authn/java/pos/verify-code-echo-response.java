// 出处:人工构造(依据 CWE-287 响应回显验证码+弱熵源)
@GetMapping("/otp")
public Map<String, String> otp(@RequestParam String phone) {
    String code = String.format("%06d", new Random().nextInt(1000000));
    smsGateway.send(phone, code);
    return Map.of("verifyCodeHint", code);
}
