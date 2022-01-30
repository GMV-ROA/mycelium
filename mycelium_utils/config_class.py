import yaml
import os 
from .utils import *


class DefaultConfig(dict):

   def __init__(self, *arg, **kw):
      super(DefaultConfig, self).__init__(*arg, **kw)
      dir_path = os.environ['MYCELIUM_CFG_ROOT']
      self.cfg_file = os.path.join(dir_path, 'default.yaml')
      cfg = yaml.safe_load(open(self.cfg_file))
      self.__dict__.update(cfg)

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


class RedisConfig(DefaultConfig):

   def __init__(self, *arg, **kw):
      super(RedisConfig, self).__init__(*arg, **kw)
      dir_path = os.environ['MYCELIUM_CFG_ROOT']
      self.cfg_file = os.path.join(dir_path, 'redis_dict.yaml')
      cfg = yaml.safe_load(open(self.cfg_file))
      self.__dict__.update(cfg)

   def generate_flat_keys(self, db):
      if isinstance(db, int):
         db = get_key_from_value(self.databases, db)

      items = self.get_key(db)
      if isinstance(items, list):
         return items

      return flatten(items)

class NetworkConfig(DefaultConfig):

   def __init__(self, *arg, **kw):
      super(NetworkConfig, self).__init__(*arg, **kw)
      dir_path = os.environ['MYCELIUM_CFG_ROOT']
      self.cfg_file = os.path.join(dir_path, 'network.yaml')
      try:
         cfg = yaml.safe_load(open(self.cfg_file))
      except:
         cfg = {}
      if cfg:
          self.__dict__.update(cfg)

      self.udp_ext = self.generate_external_ports()

   def generate_external_ports(self):
      ext = {}
      for key in self.__dict__.keys():
         if key[0] == '_':
            ip_addr_key = key[1:]
            endpoint_name = ip_addr_key+'_to_robot'
            ext[endpoint_name] = str(self.get_key(ip_addr_key))+':'+str(self.get_key(key))

      return ext

