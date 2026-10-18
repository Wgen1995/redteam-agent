// 出处:人工构造(噪音:带类型白名单 resolveClass 的安全子类——允许命中，由 C2 判别)
class LookAheadObjectInputStream extends ObjectInputStream {
    @Override
    protected Class<?> resolveClass(ObjectStreamClass desc) throws IOException, ClassNotFoundException {
        if (!ALLOWED_CLASSES.contains(desc.getName())) {
            throw new InvalidClassException("blocked class", desc.getName());
        }
        return super.resolveClass(desc);
    }
}
Object restored = safeOis.readObject();
