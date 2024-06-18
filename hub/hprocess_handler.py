from threading import Thread
from multiprocessing import Pipe

from hub.hprocess import HProcess
from utils.status import StatusCode

class HProcessHandler:
    def __init__(self, logger):
        self._processes = {}
        self._log = logger
        
        
    def create(self, game_config: dict, source_code: str, settings: dict, host_id: int) -> int:
        parent_conn, child_conn = Pipe()
        
        hprocess = HProcess(child_conn, game_config, source_code, settings)
        hprocess.start()

        comm_thread = Thread(target=self._communicate, args=(parent_conn, child_conn, hprocess.pid, host_id))
        self._processes[host_id] = [hprocess, True, parent_conn, child_conn]
        comm_thread.start()

        return hprocess.pid
    
    
    def delete(self, host_id):
        self._processes[host_id][0].kill()
        self._processes[host_id][0].join()
        self._processes[host_id][1] = False

        
    def send_data(self, host_id, data) -> StatusCode:
        self._processes[host_id][2].send(data)
        return self._processes[host_id][2].recv()['status']

    
    def _communicate(self, parent_conn, child_conn, pid, host_id):
        while self._processes[host_id][1]:
            data = parent_conn.recv()
            self._log(data['msg'], str(host_id), data['status'])
        
        self._processes[host_id][2].close()
        self._processes[host_id][3].close()
        self._processes.pop(host_id)