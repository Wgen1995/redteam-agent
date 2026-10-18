// 出处:人工构造(硬负例:WebClient JSON 外发)
reactor.core.publisher.Mono<String> resp = webClient.post().uri(hook).bodyValue(event).retrieve().bodyToMono(String.class);
