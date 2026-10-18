// 出处:人工构造(依据 CWE-502 cookie 载荷形态——b64 透传后读点)
import { unserialize } from "node-serialize";
const serializeLib = require("node-serialize");
const raw = Buffer.from(req.cookies.session, "base64").toString("utf8");
const state = serializeLib.unserialize(raw);
