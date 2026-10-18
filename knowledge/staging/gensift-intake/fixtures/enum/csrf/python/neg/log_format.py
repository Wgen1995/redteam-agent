# 出处:人工构造(硬负例:结构化日志)
import logging
logger = logging.getLogger(__name__)
def audit(actor: str, action: str) -> None:
    logger.info("actor=%s action=%s", actor, action)
