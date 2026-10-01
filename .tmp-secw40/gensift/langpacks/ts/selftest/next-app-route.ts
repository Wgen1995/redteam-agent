// selftest 样本: Next.js App Router route handler（T-SRC10/T-SRC11 预期命中）
export async function GET(request: Request) {
  const url = new URL(request.url);
  return Response.json({ path: url.pathname });
}

export async function POST(request: Request) {
  const body = await request.json();
  return Response.json({ ok: true });
}
