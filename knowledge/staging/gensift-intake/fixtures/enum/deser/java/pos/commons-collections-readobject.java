// 出处:CVE-2015-7501(Commons-Collections InvokerTransformer 链触发端形态)
ObjectInputStream ois = new ObjectInputStream(sock.getInputStream());
Object payload = ois.readObject(); // gadget 链在此实例化并触发 transform
ois.close();
