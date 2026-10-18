// 出处:人工构造(依据 CWE-918 RestTemplate 形态)
ResponseEntity<String> re = restTemplate.getForEntity(fetchUrl, String.class);
return ResponseEntity.ok(re.getBody());
