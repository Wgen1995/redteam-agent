// selftest 样本: Express 路由 + req 取参共现标记（T-SRC04..08/T-SRC15..17 预期命中）
import express from "express";
const router = express.Router();

router.get("/orders/:id", getOrder);
router.post("/orders", createOrder);
router.put("/orders/:id", updateOrder);
router.delete("/orders/:id", deleteOrder);

const app = express();
app.get("/health", healthHandler);

function search(req) {
  return `${req.query.q} ${req.body.filter} ${req.params.scope}`;
}
