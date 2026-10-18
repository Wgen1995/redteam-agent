# 出处:人工构造(from subprocess 直连导入形态)
from subprocess import Popen
Popen("nmap -p " + port + " " + host, shell=True)
