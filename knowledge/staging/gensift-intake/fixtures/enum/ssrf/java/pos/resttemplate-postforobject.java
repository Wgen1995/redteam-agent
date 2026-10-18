// 出处:人工构造(依据 CWE-918 RestTemplate webhook 形态)
String ack = restTemplate.postForObject(webhookUrl, payload, String.class);
return ack;
