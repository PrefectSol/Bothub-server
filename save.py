
class HProcessHandler:
    def __init__(self, logger):
        self._processes = {}
        self._log = logger

    def create(
        self, game_config: dict, source_code: str, settings: dict, host_id: int
    ) -> int:
        parent_conn, child_conn = Pipe()

        hprocess = HProcess(child_conn, game_config, source_code, settings)
        hprocess.start()

        comm_thread = Thread(
            target=self._communicate,
            args=(parent_conn, child_conn, hprocess.pid, host_id),
        )
        self._processes[host_id] = [hprocess, True, parent_conn, child_conn, False]
        comm_thread.start()

        return hprocess.pid

    def delete(self, host_id):
        self._processes[host_id][0].kill()
        self._processes[host_id][0].join()
        self._processes[host_id][1] = False

    def send_data(self, host_id, data) -> StatusCode:
        if self._processes[host_id][4]:
            return StatusCode.GameStarted

        try:
            self._processes[host_id][2].send(data)
            response = self._processes[host_id][2].recv()
            return response["status"]
        except Exception as e:
            self._log(
                f"Error in send_data: {str(e)}", str(host_id), StatusCode.SendDataError
            )
            return StatusCode.SendDataError

    def _communicate(self, parent_conn, child_conn, pid, host_id):
        try:
            while self._processes[host_id][1]:
                try:
                    data = parent_conn.recv()
                    if data["status"] == StatusCode.GameStarted:
                        self._processes[host_id][4] = True

                    self._log(data["msg"], str(host_id), data["status"])
                except EOFError:
                    self._log(
                        "Connection closed", str(host_id), StatusCode.ConnectionClosed
                    )
                    break
        except Exception as e:
            self._log(
                f"Error in _communicate: {str(e)}",
                str(host_id),
                StatusCode.CommunicationError,
            )

