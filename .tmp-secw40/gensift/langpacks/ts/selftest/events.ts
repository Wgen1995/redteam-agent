// selftest 样本: 事件/消息/CLI 入口形态（T-SRC12/T-SRC13/T-SRC14 预期命中）
import { Controller } from "@nestjs/common";
import { MessagePattern } from "@nestjs/microservices";

socket.on("message", (data) => handle(data));
process.on("message", (msg) => dispatch(msg));
emitter.on("connection", (sock) => attach(sock));

@Controller("jobs")
export class JobsController {
  @MessagePattern("job.run")
  run(cmd: any) { return this.executor.exec(cmd); }
}

const args = process.argv.slice(2);
