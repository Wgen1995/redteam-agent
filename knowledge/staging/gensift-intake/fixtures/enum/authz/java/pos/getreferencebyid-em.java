// 出处:人工构造(依据 CWE-639 JPA getReferenceById 形态)
@DeleteMapping("/payments/{paymentId}")
public void cancel(@PathVariable Long paymentId) {
    Payment payment = paymentRepository.getReferenceById(paymentId);
    payment.setStatus("CANCELLED");
}
