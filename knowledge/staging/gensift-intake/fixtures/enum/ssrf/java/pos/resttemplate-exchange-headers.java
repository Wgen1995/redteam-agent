// 出处:人工构造(依据 CWE-918 RestTemplate exchange 形态)
HttpHeaders headers = new HttpHeaders();
headers.set("X-Trace", traceId);
HttpEntity<String> entity = new HttpEntity<>(headers);
ResponseEntity<String> re = restTemplate.exchange(targetUri, HttpMethod.GET, entity, String.class);
