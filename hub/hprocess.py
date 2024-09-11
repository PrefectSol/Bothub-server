import time
import re
from multiprocessing import Process

from utils.status import StatusCode


class HProcess(Process):
    def __init__(
        self,
        host_id,
        bot_iqueue,
        bot_oqueue,
        log_queue,
        game_config: dict,
        source_code: str,
        settings: dict,
    ):
        super(HProcess, self).__init__()
        self._clients_count = 0
        self._bot_iqueue = bot_iqueue
        self._bot_oqueue = bot_oqueue
        self._log_queue = log_queue
        self._game_config = game_config
        self._source_code = source_code
        self._settings = settings
        self._log_data = {"msg": {}, "status": StatusCode.Unknown}

    def run(self):
        if not self.__add_class(self._game_config, self._source_code, self._settings):
            self._log_data["msg"] = "Failed to create custom class."
            self._log_data["status"] = StatusCode.FailedCreateUserClass
            self._log_queue.put(self._log_data.copy())
            return

        self._log_data["msg"] = "The host has been created from user class."
        self._log_data["status"] = StatusCode.Success
        self._log_queue.put(self._log_data.copy())

        self.__await_bots()

        self._log_data["msg"] = "The game has been started."
        self._log_data["status"] = StatusCode.GameStarted
        self._log_queue.put(self._log_data.copy())

        num_iterations = int(self._game_config["iterations"])
        for epoch in range(num_iterations):
            self._game.set_state()
            self.__log()

            while self._game.is_playing:
                self._game.step()
                self.__log(epoch=epoch)

                time.sleep(self._game_config["delay"])

        self._log_data["msg"] = f"The game has been finished"
        self._log_data["status"] = StatusCode.GameFinished
        self._log_queue.put(self._log_data.copy())

    def __await_bots(self):
        while self._clients_count < self._game.players_count:
            bot_source = self._bot_iqueue.get()
            if not self._game.add_client(bot_source):
                self._log_data["msg"] = "Failed to add bot."
                self._log_data["status"] = StatusCode.AddBotError
                self._bot_oqueue.put(self._log_data.copy())
                self._log_queue.put(self._log_data.copy())
                continue

            self._log_data["msg"] = "Bot has been successfully added."
            self._log_data["status"] = StatusCode.Success
            self._bot_oqueue.put(self._log_data.copy())
            self._log_queue.put(self._log_data.copy())

            self._clients_count += 1

    def __add_class(self, game_config: dict, source_code: str, settings: dict) -> bool:
        match = re.search("class (\\w+)", source_code)
        if not match:
            return False

        class_name = match.group(1)
        if class_name != game_config["name"]:
            return False

        try:
            exec(source_code, globals())
            self._game_class = eval(class_name)
            self._game = self._game_class(settings)
        except Exception as _:
            return False

        return True

    def __log(self, epoch=None):
        result = self._game.get_log()
        self._log_data["msg"] = {"iteration": epoch, "game_status": result}
        self._log_data["status"] = StatusCode.GameRunning
        self._log_queue.put(self._log_data.copy())
