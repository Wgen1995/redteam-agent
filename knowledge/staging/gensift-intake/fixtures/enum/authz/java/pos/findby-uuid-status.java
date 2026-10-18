// 出处:人工构造(依据 CWE-639 派生查询复合键无属主列形态)
public Export fetch(String uuid, String status) {
    return exportRepository.findByUuidAndStatus(uuid, status);
}
