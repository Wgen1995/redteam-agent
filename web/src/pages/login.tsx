import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { login, DEMO_FLAG } from "../lib/api";
import { BrandMark } from "../components/brand";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";

/**
 * GL-DS 登录页:暗色缺省+菱形标,母版 cli/webui/static/login.html @4900af6。
 * 对接 T1: POST /api/auth/login body {"key"}(dev 走 vite 代理→127.0.0.1:8901)。
 * 200 {ok:true}→/chat;401→行内错误「密钥不对」;demo:true→/chat 顶黄条。
 */
export default function LoginPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [key, setKey] = useState("");
  const [peek, setPeek] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [errInput, setErrInput] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    let out: Awaited<ReturnType<typeof login>>;
    try {
      out = await login(key);
    } catch (err) {
      out = { status: 0, ok: false, demo: false, error: "网络错误:" + String(err) };
    }
    setBusy(false);
    if (out.ok) {
      if (out.demo) sessionStorage.setItem(DEMO_FLAG, "1");
      else sessionStorage.removeItem(DEMO_FLAG);
      navigate("/chat", { replace: true });
      return;
    }
    if (out.status === 401) {
      setError(out.error || "密钥不对");
      setErrInput(true);
      inputRef.current?.focus();
      return;
    }
    setError(out.error || `登录失败(HTTP ${out.status})`);
  }

  return (
    <div className="flex min-h-dvh w-full items-center justify-center bg-bg p-6">
      <div className="w-[min(380px,92vw)] rounded-glds border border-line bg-bg-card p-8 shadow-glds">
        <div className="mb-1 flex items-center gap-2 text-acc">
          <BrandMark size={22} />
          <h1 className="text-fs-d font-semibold tracking-[0.3px] text-tx1">GraphLed</h1>
        </div>
        <p className="mb-[22px] text-fs-a leading-[1.75] text-tx4">
          授权渗透测试的观察与驾驶舱:只看授权范围内的事,每一步留痕。
        </p>
        <form onSubmit={onSubmit} noValidate>
          <label htmlFor="op-key" className="mb-2 block text-fs-a tracking-[1px] text-tx4">
            操作员密钥
          </label>
          <div className="relative">
            <Input
              ref={inputRef}
              id="op-key"
              type={peek ? "text" : "password"}
              autoComplete="current-password"
              placeholder="输入操作员密钥"
              value={key}
              onChange={(e) => {
                setKey(e.target.value);
                setErrInput(false);
              }}
              aria-invalid={errInput || undefined}
              className="pr-12"
            />
            <button
              type="button"
              onClick={() => setPeek((p) => !p)}
              aria-label="显示或隐藏密钥"
              aria-pressed={peek}
              className="absolute inset-y-0 right-0 flex cursor-pointer items-center px-3 text-tx4 hover:text-acc"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                aria-hidden="true"
              >
                <path d="M1.5 8S4 3.5 8 3.5 14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8Z" />
                <circle cx="8" cy="8" r="2" />
              </svg>
            </button>
          </div>
          <p role="alert" className="mt-2 min-h-5 text-fs-a text-dang">
            {error}
          </p>
          <Button type="submit" className="mt-[18px] w-full py-3" disabled={busy}>
            {busy && <span className="spin" aria-hidden="true" />}
            登录
          </Button>
        </form>
        <div className="mt-[14px] rounded-glds-s border border-dashed border-line-2 p-3 text-fs-a leading-[1.8] text-tx4">
          <b className="font-medium text-tx3">首次使用?</b>
          操作员密钥在服务启动日志里——启动横幅会打印一次;设{" "}
          <span className="font-mono text-tx3">TANYIN_OPERATOR_KEY</span> 可固定密钥。
        </div>
        <footer className="mt-[18px] text-fs-a leading-[1.7] text-tx5">
          GraphLed · 本系统仅用于已授权的安全测试
        </footer>
      </div>
    </div>
  );
}
