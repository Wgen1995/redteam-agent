// 出处:人工构造(依据 CWE-918 RestTemplate 形态)
String target = req.getParameter("target");
String body = restTemplate.getForObject(target, String.class);
model.addAttribute("preview", body);
