// 出处:人工构造(依据 CWE-918 注解声明式入口形态)
@PostMapping("/callback")
public ResponseEntity<String> register(@RequestParam("endpoint") String endpoint, @RequestBody Payload payload) {
    ResponseEntity<String> re = restTemplate.postForEntity(endpoint, payload, String.class);
    return ResponseEntity.status(re.getStatusCode()).body(re.getBody());
}
