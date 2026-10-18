# -*- coding: utf-8 -*-
"""业务逻辑层(功能6)——抓工具扫不出、只有懂业务才抓得到的洞。

三件: 身份矩阵装配(identity_matrix)/差分探测器(differ)/作弊假设卡模板(hypcards)。
设计: docs/design/2026-10-20-bizlogic-layer-design.md。
纪律内核: RT-0006(零差分不猜/方法族/预算警戒)+RT-0016(auth_context 挂链血律)。
考卷: evals/gt/battlefields/range-bizflow-v1.json(种子态,改价/优惠券重用/取消后发货)。
"""
from . import identity_matrix  # noqa: F401
from . import differ  # noqa: F401
from . import hypcards  # noqa: F401
