import redis
import json

class Redis:
    conn = None

    @classmethod
    def connect(cls):
        if cls.conn is None:
            cls.conn = redis.Redis(host='192.168.123.123', port=6379, db=0)

    @classmethod
    def flush_all(cls):
        cls.connect()
        cls.conn.flushall()

    @classmethod
    def flush_db(cls):
        cls.connect()
        cls.conn.flushdb()

    @classmethod
    def set(cls, key, value):
        cls.connect()
        cls.conn.set(key, json.dumps(value))

    @classmethod
    def get(cls, key):
        cls.connect()
        value = cls.conn.get(key)
        if value is not None:
            return json.loads(value.decode())
        else:
            return None




def main():
    Redis.set("key", {"key1": "value1", "key2": "value2"})
    Redis.flush_db()
    res = Redis.get("key")
    print(res)

if __name__ == "__main__":
    main()
