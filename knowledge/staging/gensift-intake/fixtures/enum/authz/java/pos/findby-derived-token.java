// 出处:人工构造(依据 CWE-639 派生查询键形谓词无属主列形态)
public ApiResponse resolve(String token) {
    return apiKeyRepository.findByToken(token);
}
