# 出处:人工构造(依据 CWE-78 shell=True 拼接形态)
import subprocess
subprocess.run("convert " + src + " -resize 50% " + dst, shell=True)
