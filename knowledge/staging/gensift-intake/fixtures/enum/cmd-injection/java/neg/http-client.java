// 出处:人工构造(硬负例:HTTP 客户端)
HttpResponse<String> resp = client.send(request, HttpResponse.BodyHandlers.ofString());
