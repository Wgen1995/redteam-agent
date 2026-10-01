// selftest 样本: Next.js Pages Router API route（T-SRC09 预期命中；req.query 共现复证 T-SRC15）
import type { NextApiRequest, NextApiResponse } from "next";

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const q = req.query.q;
  res.status(200).json({ q });
}
