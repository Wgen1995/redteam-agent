// 出处:人工构造(依据 CWE-601 OAuth 回调 relay 目标可控)
export async function GET(req: NextRequest) {
  const relay = req.nextUrl.searchParams.get("relayState") ?? "/";
  return NextResponse.redirect(relay);
}
