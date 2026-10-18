// 出处:人工构造(硬负例:外发 URL 构造,常量 host)
public URI buildRateQuery(String base) {
    return UriComponentsBuilder.fromHttpUrl("https://api.internal/rates")
        .queryParam("base", base)
        .build().toUri();
}
