// 出处:人工构造(硬负例:哈希计算)
import { createHash } from "crypto";
export function fingerprint(payload: string): string {
  return createHash("sha256").update(payload).digest("hex");
}
