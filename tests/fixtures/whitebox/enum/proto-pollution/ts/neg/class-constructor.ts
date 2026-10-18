// 出处:人工构造(硬负例:类构造器形态边界)
class Order {
  constructor(private readonly id: string, private qty: number) {}
  bump(n: number) { this.qty += n; }
}
