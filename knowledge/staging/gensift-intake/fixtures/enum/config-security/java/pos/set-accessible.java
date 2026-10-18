// 出处: 反射访问检查关闭（S1 起步集——config-security CS-J05）
public class MapperUtil {
  public Object read(Object target, Field field) throws Exception {
    field.setAccessible(true);
    return field.get(target);
  }
}
