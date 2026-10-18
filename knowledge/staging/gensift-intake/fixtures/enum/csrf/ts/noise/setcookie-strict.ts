// 出处:人工构造(噪音:fastify 全属性下发)
app.post("/login", async (req, reply) => {
  reply.setCookie("session", token, { path: "/", httpOnly: true, secure: true, sameSite: "strict" });
  return { ok: true };
});
