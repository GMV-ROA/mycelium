import redis
import json
from  mycelium.components import RedisConfig

class RedisBridge:

    DEFAULT_EXPIRY = 60*60*24 # 24 hours
    CONNECTION_ERROR = redis.exceptions.ConnectionError

    def __init__(self, host='127.0.0.1', port=6379, db=0):
        super().__init__()
        self.r = redis.Redis(host=host, port=port, db=db)
        try:
            self.r.ping()
        except redis.exceptions.ConnectionError as e:
            raise e
        
    def add_key(self, value, *keys, expiry=None, to_json=True):
        key_string = ":".join(keys)
        # print("key string: %s" % key_string)
        return self.add_key_by_string(value, key_string, expiry, to_json)

    def add_key_by_string(self, value, key_string, expiry=None, to_json=True):
        if to_json:
            value = json.dumps(value)
        
        return self.r.set(key_string, value, expiry)

    def get_key(self, *keys, parse_json=True):
        key_string = ":".join(keys)   
        # print("getting key string %s" % key_string)     
        return self.get_key_by_string(key_string, parse_json)
        
    def get_key_by_string(self, key_string, parse_json=True):
        data = self.r.get(key_string)
        if parse_json and data is not None:
            data = json.loads(data)
        return data

    def hset(self, *keys, data, mapping):
        key_string = ":".join(keys)
        value = data
        self.r.hset(key_string, value, mapping)

    def hget_all(self, *keys, value):
        key_string = ":".join(keys)

        list_of_keys = []
        keys = self.r.keys(key_string)
        for key in keys:
            list_of_keys.append(self.r.hget(key, value))

        return list_of_keys

    def send_stream(self, id, *keys, data):
        key_string = ":".join(keys)
        stream = {id: data}
        return self.r.xadd(key_string, stream, maxlen=100)

    def read_stream(self, name):
        data = self.r.xread({name:b"$"}, None, 0) # if data is empty, throw an error?
        data_stream = data[0][1][0]

        for data in data_stream:
            if isinstance(data, dict):
                encoded_data = list(data.values())[0]

                return encoded_data

