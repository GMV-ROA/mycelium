#!/usr/bin/env python3

from mycelium.components import RedisBridge, Connector
from mycelium_utils import Scripter

class ScripterExt(Scripter):

    def run_main(self):
        rb = RedisBridge(db=self.rd_cfg.databases['robot'])
        self.conn = Connector(self.cfg.ap_to_redis, self.cfg.connection_baudrate, 1, 0)
        params = self.rd_cfg.robot

        while not self.exit_threads:
            try:
                self.conn.send_heartbeat()
                m = self.conn.get_callbacks(params)
                if m is not None:
                    rb.add_key(m.to_json(), m.get_type(), to_json=False)
            except:
                pass
        
    def close_script(self):
        try:
            self.conn.disconnect()
        except:
            pass


scripter = ScripterExt(log_source="ap_to_redis")
scripter.run()