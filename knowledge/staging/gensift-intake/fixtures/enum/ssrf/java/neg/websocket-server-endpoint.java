// 出处:人工构造(硬负例:入站 WebSocket 端点)
@ServerEndpoint("/ws/notifications")
public class NotificationEndpoint {
    @OnMessage
    public void onMessage(Session session, String msg) {
        session.getAsyncRemote().sendText("pong:" + msg);
    }
}
