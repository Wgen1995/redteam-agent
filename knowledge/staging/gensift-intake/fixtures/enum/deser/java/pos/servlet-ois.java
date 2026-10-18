// 出处:CVE-2015-4852(Weblogic T3 流反序列化入口形态)
protected void doPost(HttpServletRequest request, HttpServletResponse response) throws Exception {
    ObjectInputStream ois = new ObjectInputStream(request.getInputStream());
    Object cmd = ois.readObject();
    ois.close();
}
