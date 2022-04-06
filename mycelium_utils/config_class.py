import yaml
import os 
from .utils import *


class ConfigBase(dict):
   def __init__(self, *arg, **kwargs):
      super(ConfigBase, self).__init__(*arg, **kwargs)

   def has_key(self, key):
      return key in self.__dict__

   def get_key(self, key):
      return self.__dict__[key]

   def write_key(self, value, keys):
      # if not self.has_key():
      #    return

      indent = 0
      indent_str = '  '
      lines = []
      search = True
      with open(self.cfg_file, 'r') as fileobject:
         key = keys.pop(0)
         for line in fileobject:
            if search and line[:len(key)+1] == key+':' and len(keys) > 0:
               indent += 1
               key = indent_str*indent + keys.pop(0)
               lines.append(line)
            elif search and line[:len(key)+1] == key+':' and len(keys) == 0:
               write_str = key + ': ' + str(value) + '\n'
               lines.append(write_str)
               search = False # Correct line is found
            else:
               lines.append(line)

      with open(self.cfg_file, 'w') as fileobject:
         fileobject.writelines(lines)
      
      self.__init__()    

# TODO: rename this class to something more meaningful
class DefaultConfig(ConfigBase):

   def __init__(self, *arg, **kwargs):
      super(DefaultConfig, self).__init__(*arg, **kwargs)
      dir_path = os.environ['MYCELIUM_CFG_ROOT']
      cfg_file = kwargs.get('cfg_file', 'default.yaml')
      print("Using config file: ", cfg_file)
      self.cfg_file = os.path.join(dir_path, cfg_file)
      cfg = yaml.safe_load(open(self.cfg_file))
      self.__dict__.update(cfg)

   def get_redis_connection(self):

      host = self.network['default_redis_host']
      port = self.network['default_redis_port']

      if "REDIS_HOST_IP" in os.environ:
         host = os.environ['REDIS_HOST_IP']

      if "REDIS_HOST_PORT" in os.environ:
         port = os.environ['REDIS_HOST_PORT']

      return (host,port)


class RedisConfig(ConfigBase):

   def __init__(self, *arg, **kwargs):
      super(RedisConfig, self).__init__(*arg, **kwargs)
      dir_path = os.environ['MYCELIUM_CFG_ROOT']
      dict_file = kwargs.get('dict_file', 'redis_dict.yaml')
      print("Using dict file: ", dict_file)
      self.cfg_file = os.path.join(dir_path, dict_file)
      cfg = yaml.safe_load(open(self.cfg_file))
      self.__dict__.update(cfg)

   def generate_flat_keys(self, db):
      if isinstance(db, int):
         db = get_key_from_value(self.databases, db)

      items = self.get_key(db)
      if isinstance(items, list):
         return items

      return flatten(items)


class NetworkConfig(ConfigBase):

   def __init__(self, *arg, **kwargs):
      super(NetworkConfig, self).__init__(*arg, **kwargs)
      dir_path = os.environ['MYCELIUM_CFG_ROOT']
      net_file = kwargs.get('net_file', 'network.yaml')
      print("Using network file: ", net_file)
      self.cfg_file = os.path.join(dir_path, net_file)
      try:
         cfg = yaml.safe_load(open(self.cfg_file))
         self.__dict__.update(cfg)
      except:
         cfg = {}
      cfg = {}

      self.udp_ext = self.generate_external_ports()

   def generate_external_ports(self):
      ext = {}
      for key in self.__dict__.keys():
         if key[0] == '_':
            ip_addr_key = key[1:]
            endpoint_name = ip_addr_key+'_to_robot'
            ext[endpoint_name] = str(self.get_key(ip_addr_key))+':'+str(self.get_key(key))

      return ext

