# selftest 样本: Django Channels consumer 消息入口（P-SRC15 预期命中）
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None):
        payload = json.loads(text_data)
        await self.channel_layer.group_send("chat", payload)
