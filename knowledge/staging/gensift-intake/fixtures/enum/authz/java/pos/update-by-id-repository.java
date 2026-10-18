// 出处:人工构造(依据 CWE-639 按 id 定位更新且请求体整体透传形态)
@PutMapping("/profiles/{userId}")
public void update(@PathVariable Long userId, @RequestBody ProfileDto dto) {
    profileRepository.updateProfile(userId, dto);
}
