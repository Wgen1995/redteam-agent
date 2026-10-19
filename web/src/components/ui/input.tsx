import * as React from "react";
import { cn } from "../../lib/utils";

/** GL-DS 输入框(shadcn 结构):bg-side 底+line-2 边,focus 转 acc2,错误态 dang 红边。 */
function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex w-full rounded-glds-s border border-line-2 bg-bg-side px-3 py-2 text-fs-b text-tx1 transition-colors placeholder:text-tx5 focus-visible:border-acc2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 aria-[invalid=true]:border-dang",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
