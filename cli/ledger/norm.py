# -*- coding: utf-8 -*-
"""证据工件双指纹 norm 轨单源（批次 4 评审 C-1 收口）——写路径（add-evidence 落账
E-index.content_hash_norm）与查路径（hash-recheck 重算）共用本模块，禁再分叉。
分叉史（C-1 根因）：write_cmds._hashes 整行丢弃（_NORM_DROP）+<TS>+splitlines/join
vs check_cmds.normalize_artifact 值替换+<ts>+split/join——语义不同致真实铸造工件
落账 norm 恒不等于重算 norm（哨兵大小写+尾换行结构两处系统性失配）。

归一化规则冻结（哨兵语义=严格侧：除下列动态字段外，工件改一字必被 norm 轨检出；
整行丢弃类宽松归一化禁用——动态字段所在行的其余内容同样受保护）：
  1. 解码 utf-8（errors="replace"）——二进制工件 norm 轨恒可定义（U+FFFD 确定性
     替换；原写路径「不可解码=norm 退化 raw」分支退役）；
  2. 删 CR——跨平台行尾归一；
  3. ISO8601 时间戳（YYYY-MM-DD[T ]HH:MM:SS(.frac)?(Z|±HH[:MM])?）→ 哨兵 <ts>；
  4. epoch 秒（1[6-9] 接 8 位数字，词边界）→ 哨兵 <ts>；
  5. nonce/csrf 值（键[=:]值，值=[^\s;]+）→「键=<n>」——仅替换值，键与行内其余
     字符全部保留（对照写路径旧 _NORM_DROP 整行丢弃=宽松侧，弃用）；
  6. 逐行 rstrip + split/join（"\n"）——尾随空行/结尾换行结构保留（对照写路径旧
     splitlines/join：结尾换行丢失=任何带尾换行文本工件恒失配）。
哨兵 <ts>/<n> 定死小写。动态字段清单即本 docstring——增删归一化规则=面变更，
须走版本化通道（契约 02a hash-recheck 节注记）。
"""
import hashlib
import re

_ISO_TS = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?")
_EPOCH_S = re.compile(r"\b1[6-9]\d{8}\b")
_NONCE = re.compile(r"(?i)\b(nonce|csrf)\s*[=:]\s*[^\s;]+")


def normalize_artifact(text):
    """norm 轨归一化（规则冻结见模块 docstring；单源——写/查两路禁自带副本）。"""
    t = text.replace("\r", "")
    t = _ISO_TS.sub("<ts>", t)
    t = _EPOCH_S.sub("<ts>", t)
    t = _NONCE.sub(r"\1=<n>", t)
    return "\n".join(ln.rstrip() for ln in t.split("\n"))


def artifact_hashes(data):
    """E-index content_hash 双轨单源：raw=原始字节 sha256；norm=归一化文本 sha256。
    data=工件原始字节（缺失工件由调用方传 b""——add-evidence 缺工件语义不变）。"""
    raw = hashlib.sha256(data).hexdigest()
    norm = hashlib.sha256(
        normalize_artifact(data.decode("utf-8", "replace")).encode("utf-8")).hexdigest()
    return raw, norm
