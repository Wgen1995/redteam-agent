// 出处:人工构造(依据 CWE-918 WebClient 形态)
String body = webClient.get().uri(imageUrlParam).retrieve().bodyToMono(String.class).block();
return ResponseEntity.ok(body);
