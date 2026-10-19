import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

/**
 * GL-DS 按钮(手搓,shadcn 结构:cva 变体+cn 合并)。
 * 裁决记录: shadcn CLI 4.22.1 init 在非交互环境 preflight 失败
 * (要求先有 tailwind 导入+路径别名),按预授权裁决手搓最小件。
 */
const buttonVariants = cva(
  "inline-flex cursor-pointer items-center justify-center gap-2 whitespace-nowrap rounded-glds-s font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-acc2 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-60",
  {
    variants: {
      variant: {
        default: "border border-acc2 bg-acc2 text-acc-on hover:bg-acc",
        outline:
          "border border-line-2 bg-transparent text-tx2 hover:border-tx5 hover:bg-bg-raise",
        ghost: "border border-transparent bg-transparent text-tx3 hover:bg-bg-hover hover:text-tx2",
        destructive: "border border-dang bg-dang text-tx1 hover:opacity-90",
      },
      size: {
        default: "px-4 py-2.5 text-fs-b",
        sm: "px-3 py-1.5 text-fs-a",
        lg: "px-5 py-3 text-fs-c",
        icon: "h-9 w-9 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

function Button({
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants>) {
  return (
    <button
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
