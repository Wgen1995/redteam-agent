// 出处:人工构造(依据 CWE-502 XMLDecoder 形态——new 即绑定输入流)
XMLDecoder dec = new XMLDecoder(new ByteArrayInputStream(xmlBytes));
Object result = dec.readObject();
dec.close();
