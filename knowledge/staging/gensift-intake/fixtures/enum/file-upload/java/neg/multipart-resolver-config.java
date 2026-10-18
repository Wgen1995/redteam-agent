// 出处:人工构造(硬负例:multipart 解析器配置——MultipartResolver 无文件落盘)
@Bean
public org.springframework.web.multipart.commons.CommonsMultipartResolver multipartResolver() {
    org.springframework.web.multipart.commons.CommonsMultipartResolver r = new org.springframework.web.multipart.commons.CommonsMultipartResolver();
    r.setMaxUploadSize(5242880L);
    return r;
}
