// 出处:人工构造(依据 CWE-352 fastify reply.setCookie 无 Strict 兜底)
app.post("/login", async (req, reply) => {
  const token = sessionManager.open(req.body);
  reply.setCookie("session", token, { path: "/", sameSite: "none" });
  return { ok: true };
});
