# 出处:人工构造(噪音:filter_by 带属主列)
def load(iid, uid):
    row = session.query(Item).filter_by(id=iid, owner_id=uid).one()
    return row
