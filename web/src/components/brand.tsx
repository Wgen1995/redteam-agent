/** GraphLed 菱形标(GL-DS 母版原 path)。 */
export function BrandMark({
  size = 22,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      aria-hidden="true"
      className={className}
    >
      <path d="M8 1.6 14.4 8 8 14.4 1.6 8Z" />
    </svg>
  );
}
