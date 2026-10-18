// 出处: actuator 端点暴露（S1 起步集——config-security CS-J08）
// application.properties 等价转录（properties 载体在清单内为 config 角色）:
// management.endpoints.web.exposure.include=*
public class ActuatorTranscribe {
  String exposureKey = "management.endpoints.web.exposure.include";
}
