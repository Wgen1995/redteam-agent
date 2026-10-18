// 出处:人工构造(噪音:声明式 @PreAuthorize 守卫下的 findById)
@PreAuthorize("@documentGuard.check(#id, authentication)")
@GetMapping("/documents/{id}")
public Document read(@PathVariable Long id) {
    return documentRepository.findById(id).orElseThrow();
}
