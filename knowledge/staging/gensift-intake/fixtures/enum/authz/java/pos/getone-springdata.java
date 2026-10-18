// 出处:人工构造(依据 CWE-639 Spring Data getOne 惰性引用形态)
@PatchMapping("/cards/{cardId}")
public ResponseEntity<Void> freeze(@PathVariable Long cardId) {
    Card card = cardRepository.getOne(cardId);
    card.setFrozen(true);
    return ResponseEntity.ok().build();
}
