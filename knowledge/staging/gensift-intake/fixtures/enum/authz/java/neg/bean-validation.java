// 出处:人工构造(硬负例:入参约束校验)
Set<ConstraintViolation<QuoteRequest>> violations = validator.validate(quoteRequest);
if (!violations.isEmpty()) { throw new ConstraintViolationException(violations); }
