// 出处:人工构造(硬负例:事件订阅无按键取对象)
bus.on("cart.closed", (event) => { counters.close += 1; });
