// 出处:人工构造(依据 CWE-918 java.net.http.HttpClient 形态)
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder().uri(URI.create(userUrl)).build();
HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
