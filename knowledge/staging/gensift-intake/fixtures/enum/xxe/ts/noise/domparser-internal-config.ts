// 出处:人工构造(噪音:FP 卡形态——只解析服务端常量,需来源证据;命中登记)
const BUILTIN_XSLT = '<?xml version="1.0"?><xsl:stylesheet version="1.0"></xsl:stylesheet>';
const styleDoc = new DOMParser().parseFromString(BUILTIN_XSLT, 'application/xml');
