import time

from threading import Thread
from multiprocessing import Queue

from hub.hprocess import HProcess
from utils.status import StatusCode


class HProcessHandler:
    def __init__(self, logger):
        self._processes = {}
        self._log = logger

    def create(
        self, game_config: dict, source_code: str, settings: dict, host_id: int
    ) -> int:
        bot_iqueue = Queue()
        bot_oqueue = Queue()
        log_queue = Queue()

        hprocess = HProcess(
            host_id,
            bot_iqueue,
            bot_oqueue,
            log_queue,
            game_config,
            source_code,
            settings,
        )
        self._processes[host_id] = [
            hprocess,
            bot_iqueue,
            bot_oqueue,
            log_queue,
            True,
            False,
            StatusCode.Unknown,
            Thread(target=self._communicate, args=(host_id)),
        ]
        hprocess.start()
        self._processes[host_id][7].start()

        return hprocess.pid

    def delete(self, host_id):
        self._processes[host_id][0].kill()
        self._processes[host_id][0].join()
        self._processes[host_id][4] = False
        self._processes[host_id][1].close()
        self._processes[host_id][2].close()
        self._processes[host_id][3].close()
        self._processes.pop(host_id, None)

    def send_data(self, host_id, data) -> StatusCode:
        if host_id not in self._processes:
            return StatusCode.UnknownHost

        if self._processes[host_id][5]:
            return StatusCode.GameStarted

        try:
            self._processes[host_id][1].put(data)
            response = self._processes[host_id][2].get()
        except Exception as e:
            self._log(
                f"Error in send_data: {e}", str(host_id), StatusCode.SendDataError
            )
            return StatusCode.SendDataError

        return response["status"]

    def _communicate(self, host_id):
        try:
            while self._processes[host_id][4]:
                data = self._processes[host_id][3].get()
                if data["status"] == StatusCode.GameStarted:
                    self._processes[host_id][5] = True
                elif (
                    data["status"] == StatusCode.FailedCreateUserClass
                    or data["status"] == StatusCode.GameFinished
                ):
                    self._processes[host_id][4] = False

                self._log(data["msg"], str(host_id), data["status"])

        except Exception as e:
            self._log(
                f"Error in _communicate: {str(e)}",
                str(host_id),
                StatusCode.CommunicationError,
            )
        finally:
            self.delete(host_id)
