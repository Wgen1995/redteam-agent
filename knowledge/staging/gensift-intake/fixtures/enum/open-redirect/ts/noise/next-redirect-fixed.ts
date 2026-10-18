// 出处:人工构造(噪音:固定站内 URL)
export async function GET(req: NextRequest) {
  return NextResponse.redirect(new URL("/login", req.url));
}
