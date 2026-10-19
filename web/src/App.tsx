import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import LoginPage from "./pages/login";
import ChatPage from "./pages/chat";
import TasksPage from "./pages/tasks";
import TaskDetailPage from "./pages/task-detail";
import PlaceholderPage from "./pages/placeholder";
import { AppShell } from "./app/shell";
import { ALL_ITEMS } from "./app/ia";

/**
 * P0 T4 路由骨架: /login 独立成页;其余 20 页住壳(侧栏+顶栏+Outlet)。
 * /chat=指挥台实页(T5 接时刻流);其余 19 页统一占位空态。
 */
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<AppShell />}>
          <Route path="/chat" element={<ChatPage />} />
          {/* T11 任务列表+详情·会话签(20 页 IA 外深链页,仗卡自指挥流数据) */}
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/tasks/:id" element={<TaskDetailPage />} />
          {ALL_ITEMS.filter((i) => i.path !== "/chat").map((i) => (
            <Route
              key={i.path}
              path={i.path}
              element={<PlaceholderPage name={i.name} hint={i.hint} />}
            />
          ))}
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
