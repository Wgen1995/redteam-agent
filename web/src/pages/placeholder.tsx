/** 统一空态占位页(P0 T4): 页名+一句指路文案(IA 单源 web/src/app/ia.ts)。
 *
 * 除 /chat(指挥台实页)外 19 页共用;后续任务逐页替换为实页。
 */
export default function PlaceholderPage({ name, hint }: { name: string; hint: string }) {
  return (
    <section
      data-testid="placeholder-page"
      className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center"
    >
      <h1 className="text-fs-d font-medium text-tx2">{name}</h1>
      <p className="max-w-md text-fs-b leading-[1.8] text-tx4">{hint}</p>
    </section>
  );
}
