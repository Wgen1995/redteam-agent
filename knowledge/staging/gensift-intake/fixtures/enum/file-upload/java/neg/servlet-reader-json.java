// 出处:人工构造(硬负例:原生 reader 读 JSON)
StringBuilder buf = new StringBuilder();
req.getReader().lines().forEach(buf::append);
com.fasterxml.jackson.databind.JsonNode node = mapper.readTree(buf.toString());
