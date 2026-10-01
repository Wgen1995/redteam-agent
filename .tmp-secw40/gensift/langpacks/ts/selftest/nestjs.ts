// selftest 样本: NestJS 装饰器即入口（T-SRC01/T-SRC02/T-SRC03 预期命中）
import { Controller, Get, Post, Body, Param } from "@nestjs/common";

@Controller("users")
export class UsersController {
  @Get(":id")
  findOne(@Param("id") id: string) { return this.svc.get(id); }

  @Post("profile")
  update(@Body() dto: ProfileDto) { return this.svc.save(dto); }
}
