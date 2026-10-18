// 出处:人工构造(硬负例:静态资源映射只读面)
@Override
public void addResourceHandlers(org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry registry) {
    registry.addResourceHandler("/assets/**").addResourceLocations("classpath:/static/");
}
