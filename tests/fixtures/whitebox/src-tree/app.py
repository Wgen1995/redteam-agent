import os


def validate(user_id):
    return int(user_id)


class Api:
    def __init__(self, conn):
        self.conn = conn

    def load_user(self, user_id):
        return validate(user_id)

    def query(self, name):
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM users WHERE n = '{name}'")
        return cur.fetchall()


def handler(name):
    api = Api(None)
    api.query(name)
    return os.getpid()
