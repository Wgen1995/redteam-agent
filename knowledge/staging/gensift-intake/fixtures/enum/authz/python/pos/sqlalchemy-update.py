# 出处:人工构造(依据 CWE-639 按 id 定位更新无属主列形态)
def close(ticket_id, actor):
    stmt = update(Ticket).where(Ticket.id == ticket_id).values(status="closed", closed_by=actor)
    session.execute(stmt)
