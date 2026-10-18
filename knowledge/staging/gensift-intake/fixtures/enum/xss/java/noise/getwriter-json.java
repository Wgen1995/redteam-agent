// 出处:人工构造(噪音:JSON 序列化内容型响应,无 HTML 上下文)
response.getWriter().print(objectMapper.writeValueAsString(dto));
