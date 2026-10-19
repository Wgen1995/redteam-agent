/** 20 页 IA 单源(P0 T4,总案 v3 §信息架构): 分组/路径/页名/占位指路文案。
 *
 * 作战 7 + 机组 4 + 系统 9 = 20 页;/chat 为指挥台实页,其余 19 页占位。
 * 指路文案一句,缺什么就说什么——零假数,不编造页面内容。
 */

export interface NavItem {
  path: string;
  name: string;
  /** 占位页指路一句(/chat 实页不用)。 */
  hint: string;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "作战",
    items: [
      { path: "/chat", name: "指挥台", hint: "" },
      {
        path: "/dashboard",
        name: "仪表盘",
        hint: "还没打过仗→去指挥台说一句打哪",
      },
      {
        path: "/mission",
        name: "任务",
        hint: "仗开了才有任务可看→先去指挥台点火",
      },
      {
        path: "/findings",
        name: "发现",
        hint: "发现随仗入账→先去指挥台开一仗",
      },
      {
        path: "/assets",
        name: "资产与覆盖",
        hint: "目标资产随仗测绘→先去指挥台开一仗",
      },
      {
        path: "/traffic",
        name: "流量",
        hint: "流量回放 P1 接线→先在指挥台看时刻流",
      },
      {
        path: "/fleet",
        name: "舰队",
        hint: "多仗同开这里排队列→现在去指挥台打第一仗",
      },
    ],
  },
  {
    label: "机组",
    items: [
      {
        path: "/tool-runs",
        name: "工具执行",
        hint: "工具流水随仗产生→先去指挥台开一仗",
      },
      {
        path: "/llm-recordings",
        name: "LLM录制",
        hint: "录制库 P1 接线→先去指挥台",
      },
      {
        path: "/reports",
        name: "报告",
        hint: "仗打完签发报告→先去指挥台开一仗",
      },
      {
        path: "/knowledge",
        name: "知识库",
        hint: "复盘蒸馏入库后可查→先打一仗",
      },
    ],
  },
  {
    label: "系统",
    items: [
      { path: "/agents", name: "智能体", hint: "智能体管理 P1 接线→先去指挥台" },
      { path: "/skills", name: "Skill", hint: "Skill 管理 P2 接线→先去指挥台" },
      { path: "/capabilities", name: "能力", hint: "考卷+棘轮 P2 接线→先去指挥台" },
      {
        path: "/intercepts",
        name: "拦截规则",
        hint: "规则五段 P1 接线→先看引擎侧配置",
      },
      {
        path: "/approvals",
        name: "审批",
        hint: "待审在指挥台气泡里批→红点亮起去处理",
      },
      { path: "/notifications", name: "通知", hint: "通知通道 P2 接线→先去指挥台" },
      {
        path: "/llm-connections",
        name: "LLM连接",
        hint: "连接管理 P3 接线→先去指挥台",
      },
      { path: "/logs", name: "日志", hint: "日志检索 P3 接线→引擎日志在仓内" },
      { path: "/settings", name: "设置", hint: "系统设置 P3 接线→先去指挥台" },
    ],
  },
];

/** 20 项摊平(路由骨架/侧栏共用)。 */
export const ALL_ITEMS: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);
