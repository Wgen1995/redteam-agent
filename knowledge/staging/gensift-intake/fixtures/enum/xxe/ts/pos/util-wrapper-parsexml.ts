// 出处:人工构造(依据 CWE-611 工具类封装形态)
export function parseXml(text: string): Document {
  return new DOMParser().parseFromString(text, 'application/xml');
}
export function firstNode(doc: Document, tag: string): string | null {
  return doc.getElementsByTagName(tag)[0]?.textContent ?? null;
}
