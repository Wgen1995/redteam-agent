// 出处: 字符串工具（neg）
public class Slug {
  public static String of(String input) {
    return input.trim().toLowerCase().replace(" ", "-");
  }
}
