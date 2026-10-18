# 出处:人工构造(噪音:list 形式不走 shell——允许命中,由五步判别)
import subprocess
subprocess.run(["ls", "-l", target_dir], check=True)
