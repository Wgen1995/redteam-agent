# 出处:人工构造(噪音:属主条件进 update 的 where)
def close(ticket_id, actor):
    stmt = update(Ticket).where(and_(Ticket.id == ticket_id, Ticket.owner_id == actor)).values(status="closed")
    session.execute(stmt)
