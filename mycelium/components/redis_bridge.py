import redis
import json
from  mycelium.components import RedisConfig

class RedisBridge:

    DEFAULT_EXPIRY = 60*60*24 # 24 hours
    CONNECTION_ERROR = redis.exceptions.ConnectionError

    def __init__(self, port=6379, db=0):
        super().__init__()
        self.r = redis.Redis(host='localhost', port=port, db=db)
        try:
            self.r.ping()
        except redis.exceptions.ConnectionError as e:
            raise e
        
    def add_key(self, value, *keys, expiry=None, to_json=True):
        key_string = ":".join(keys)
        print("key string: %s" % key_string)
        return self.add_key_by_string(value, key_string, expiry, to_json)

    def add_key_by_string(self, value, key_string, expiry=None, to_json=True):
        if to_json:
            value = json.dumps(value)
        
        return self.r.set(key_string, value, expiry)

    def get_key(self, *keys, parse_json=True):
        key_string = ":".join(keys)   
        print("getting key string %s" % key_string)     
        return self.get_key_by_string(key_string, parse_json)
        
    def get_key_by_string(self, key_string, parse_json=True):
        data = self.r.get(key_string)
        if parse_json and data is not None:
            data = json.loads(data)
        return data
