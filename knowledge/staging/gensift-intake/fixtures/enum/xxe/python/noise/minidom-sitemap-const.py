# 出处:人工构造(噪音:同 API 安全用法——解析服务端常量模板)
from xml.dom import minidom

SITEMAP_TEMPLATE = '<?xml version="1.0"?><urlset></urlset>'

def base_sitemap():
    return minidom.parseString(SITEMAP_TEMPLATE)
