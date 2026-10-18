// 出处:人工构造(噪音:验证码限次+独立计数)
@PostMapping("/otp/verify")
public void verify(@RequestBody OtpRequest req) {
    if (attemptCounter.exceeded(req.phone())) throw new ResponseStatusException(TOO_MANY_REQUESTS);
    if (!smsGateway.verifyCode(req.phone(), req.code())) throw new ResponseStatusException(UNAUTHORIZED);
    attemptCounter.reset(req.phone());
}
