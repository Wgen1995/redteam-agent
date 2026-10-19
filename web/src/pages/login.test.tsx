import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import LoginPage from "./login";
import ChatPage from "./chat";
import { DEMO_FLAG } from "../lib/api";

/** T3 登录页三用例:成功跳转 / 401 行内错误 / demo 黄条。fetch 全 mock,不碰网。 */

function mockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({ status, json: async () => body });
}

function renderApp() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("登录页", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    cleanup();
  });

  it("密钥正确(200 {ok:true})→跳转 /chat,且不挂演示标记", async () => {
    const fetchMock = mockFetch(200, { ok: true });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    renderApp();

    await user.type(screen.getByLabelText("操作员密钥"), "op-key-1");
    await user.click(screen.getByRole("button", { name: "登录" }));

    await waitFor(() =>
      expect(screen.getByTestId("chat-page")).toBeInTheDocument(),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ key: "op-key-1" }),
      }),
    );
    expect(sessionStorage.getItem(DEMO_FLAG)).toBeNull();
  });

  it("密钥不对(401)→行内错误「密钥不对」,留在登录页", async () => {
    vi.stubGlobal("fetch", mockFetch(401, { error: "密钥不对" }));
    const user = userEvent.setup();
    renderApp();

    await user.type(screen.getByLabelText("操作员密钥"), "wrong-key");
    await user.click(screen.getByRole("button", { name: "登录" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("密钥不对");
    expect(screen.queryByTestId("chat-page")).not.toBeInTheDocument();
  });

  it("演示模式(响应含 demo:true)→/chat 顶部黄条「演示模式:未设密钥」", async () => {
    vi.stubGlobal("fetch", mockFetch(200, { ok: true, demo: true }));
    const user = userEvent.setup();
    renderApp();

    await user.type(screen.getByLabelText("操作员密钥"), "anything");
    await user.click(screen.getByRole("button", { name: "登录" }));

    const banner = await screen.findByRole("status");
    expect(banner).toHaveTextContent("演示模式:未设密钥");
    expect(sessionStorage.getItem(DEMO_FLAG)).toBe("1");
  });
});
