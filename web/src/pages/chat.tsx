import { BrandMark } from "../components/brand";
import { DEMO_FLAG } from "../lib/api";

/** 指挥台占位页(T4 建壳)。演示登录(响应 demo:true)时顶部挂黄条。 */
export default function ChatPage() {
  const demo = sessionStorage.getItem(DEMO_FLAG) === "1";
  return (
    <main
      data-testid="chat-page"
      className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6"
    >
      {demo && (
        <div
          role="status"
          className="w-full max-w-3xl rounded-glds-s border border-warn/50 bg-warn/10 px-3 py-2 text-fs-a text-warn"
        >
          演示模式:未设密钥
        </div>
      )}
      <div className="flex items-center gap-2 text-tx4">
        <BrandMark size={16} />
        <p className="text-fs-a">指挥台·占位页(T4 建壳)</p>
      </div>
    </main>
  );
}
