// 出处:人工构造(噪音:@PostAuthorize 返回值属主校验下的 getOne)
@PostAuthorize("returnObject.owner == authentication.name")
public User read(Long id) {
    return userRepository.getOne(id);
}
