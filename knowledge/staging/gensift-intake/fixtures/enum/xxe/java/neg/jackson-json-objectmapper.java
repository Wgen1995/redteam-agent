// 出处:人工构造(硬负例:Jackson JSON 而非 XmlMapper)
com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
Dto dto = mapper.readValue(payload, Dto.class);
