// 出处:人工构造(硬负例:事件总线发布)
export function emitOrderPlaced(bus: EventBus, order: Order) {
  bus.publish("order.placed", { orderId: order.id, total: order.total });
}
