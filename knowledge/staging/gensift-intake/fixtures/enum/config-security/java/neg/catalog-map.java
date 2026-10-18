// 出处: 集合初始化（neg）
import java.util.Map;
import java.util.HashMap;
public class Catalog {
  private final Map<String, Integer> prices = new HashMap<>();
  public void seed() { prices.put("sku-1", 100); }
}
