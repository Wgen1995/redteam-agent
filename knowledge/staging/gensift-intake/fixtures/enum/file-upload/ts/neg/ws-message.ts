// 出处:人工构造(硬负例:WebSocket 消息)
ws.on('message', (data: Buffer) => bus.publish('chat', data.toString()));
