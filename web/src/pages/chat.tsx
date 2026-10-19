import { BrandMark } from "../components/brand";

/** 指挥台(T5 接时刻流;现为壳内占位内容,demo 黄条已挪壳顶栏)。 */
export default function ChatPage() {
  return (
    <section
      data-testid="chat-page"
      className="flex h-full flex-col items-center justify-center gap-4 p-6"
    >
      <div className="flex items-center gap-2 text-tx4">
        <BrandMark size={16} />
        <p className="text-fs-a">指挥台·占位页(T5 时刻流接线)</p>
      </div>
    </section>
  );
}
