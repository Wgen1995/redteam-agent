// 出处:人工构造(噪音:findById 后属主比对——sink 在,由五步判别,见 classes/fixture-spec.md §2)
public Document read(Long id, Principal principal) {
    Document doc = documentRepository.findById(id).orElseThrow();
    if (!doc.getOwnerId().equals(principal.getName())) {
        throw new AccessDeniedException("not owner");
    }
    return doc;
}
