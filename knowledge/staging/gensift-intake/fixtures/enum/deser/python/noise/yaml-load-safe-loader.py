# 出处:人工构造(噪音:同 API 显式指定 SafeLoader——允许命中，由 C2 判别)
cfg = yaml.load(text, Loader=yaml.SafeLoader)
