import argparse
import json
import threading
import signal
import time
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, render_template_string, send_file

from utils.status import StatusCode, HttpCode
from utils.permissions import Permissions
from utils.base import Base


class Platform(Base):
    def __init__(self, opt):
        self._database_path = "/bothub-platform/database/"
        super().__init__(self._database_path)

        try:
            with open(opt.config, "r") as file:
                config = json.load(file)
                self._max_file_size_mb = config["max_file_size_mb"]
                self._platform_file = config["platform-file"]
                self._host = config["host"]
                self._port = config["port"]
                self._is_debug = config["debug"]
                self._updater_every_hours = config["update_every_hours"]
                self._updater_delay_seconds = config["updater_delay_seconds"]
                self._encoder = config["encoding-std"]
        except Exception as exc:
            self._is_init = False
            self.plog(f"Error loading the config: {exc}", StatusCode.LoadConfigError)
            return

        signal.signal(signal.SIGTERM, self.__stop)
        signal.signal(signal.SIGUSR1, self.__switch_net)

        self.init_base(self._encoder, self._platform_file)
        self.run_updater(self._updater_every_hours, self._updater_delay_seconds)

        self._app = Flask(__name__)

        self._app.add_url_rule("/auth", view_func=self.__auth, methods=["POST"])
        self._app.add_url_rule("/deauth", view_func=self.__deauth, methods=["POST"])
        self._app.add_url_rule(
            "/createhost", view_func=self.__create_host, methods=["POST"]
        )
        self._app.add_url_rule(
            "/deletehost", view_func=self.__delete_host, methods=["POST"]
        )
        self._app.add_url_rule("/postbot", view_func=self.__post_bot, methods=["POST"])
        self._app.add_url_rule("/view", view_func=self.__view, methods=["POST"])
        self._app.add_url_rule(
            "/database/",
            defaults={"req_path": ""},
            view_func=self.__dir_listing,
            methods=["GET"],
        )
        self._app.add_url_rule(
            "/database/<path:req_path>", view_func=self.__dir_listing, methods=["GET"]
        )

        self._app.config["MAX_CONTENT_LENGTH"] = self._max_file_size_mb * 1024 * 1024

        self._is_init = True
        self._is_run = True
        self._is_enable_net = False
        self._socket_thread = threading.Thread(target=self.__run_socket, daemon=True)
        self.plog("The platform has been successfully initialized.", StatusCode.Success)

    def __del__(self):
        self.plog("Finished.", StatusCode.Finished)

    def __dir_listing(self, req_path=""):
        BASE_DIR = "database"
        abs_path = os.path.join(BASE_DIR, req_path)

        if not os.path.exists(abs_path):
            return "Not Found", HttpCode.NotFound.value

        if os.path.isfile(abs_path):
            return send_file(abs_path)

        files_and_dirs = os.listdir(abs_path)
        files_and_dirs = [os.path.join(req_path, fad) for fad in files_and_dirs]
        return render_template_string(
            """
        <ul>
            {% for item in items %}
            <li><a href="{{ item }}">{{ item }}</a></li>
            {% endfor %}
        </ul>
        """,
            items=files_and_dirs,
        )

    def __view(self):
        if not self._is_enable_net:
            return {
                "error": "Network module is disabled."
            }, HttpCode.ServiceUnvaliable.value

        data = request.get_json()
        if not "user_id" in data or not "user_sign" in data:
            return {
                "error": "The user parameters is not sets."
            }, HttpCode.BadRequest.value

        if self.is_view(data["user_id"], data["user_sign"]):
            return {
                "msg": f"http://{self._host}:{self._port}/database"
            }, HttpCode.Ok.value

        return {
            "error": "Unknown error. See the logs..."
        }, HttpCode.InternalServerError.value

    def __post_bot(self):
        if not self._is_enable_net:
            return {
                "error": "Network module is disabled."
            }, HttpCode.ServiceUnvaliable.value

        data = request.get_json()

        if not "user_id" in data or not "user_sign" in data:
            return {
                "error": "The user parameters is not sets."
            }, HttpCode.BadRequest.value

        if not "host_id" in data:
            return {"error": "The host_id is not set."}, HttpCode.BadRequest.value

        if not "bot_source" in data:
            return {"error": "The bot_source is not set."}, HttpCode.BadRequest.value

        result_code = self.post_bot(
            data["user_id"], data["user_sign"], data["bot_source"], data["host_id"]
        )

        if result_code == StatusCode.GameStarted:
            return {
                "msg": f'The game is already running. The bot cannot be added to the game: {data["host_id"]}.'
            }, HttpCode.ServiceUnvaliable.value
        elif result_code == StatusCode.UnknownHost:
            return {"msg": "The host is not exists."}, HttpCode.ServiceUnvaliable.value
        elif result_code == StatusCode.Success:
            return {
                "msg": f'Bot has been successfully posted on host {data["host_id"]}.'
            }, HttpCode.Ok.value

        return {
            "error": "Unknown error. See the logs..."
        }, HttpCode.InternalServerError.value

    def __delete_host(self):
        if not self._is_enable_net:
            return {
                "error": "Network module is disabled."
            }, HttpCode.ServiceUnvaliable.value

        data = request.get_json()
        if not "user_id" in data or not "user_sign" in data:
            return {
                "error": "The user parameters is not sets."
            }, HttpCode.BadRequest.value

        if not "host_id" in data:
            return {"error": "The host_id is not set."}, HttpCode.BadRequest.value

        result_code = self.delete_host(
            data["user_id"], data["user_sign"], data["host_id"]
        )
        if result_code == StatusCode.Success:
            return {
                "msg": f'Host {data["host_id"]} has been successfully deleted.'
            }, HttpCode.Ok.value

        return {
            "error": "Unknown error. See the logs..."
        }, HttpCode.InternalServerError.value

    def __create_host(self):
        if not self._is_enable_net:
            return {
                "error": "Network module is disabled."
            }, HttpCode.ServiceUnvaliable.value

        data = request.get_json()
        if not "user_id" in data or not "user_sign" in data:
            return {
                "error": "The user parameters is not sets."
            }, HttpCode.BadRequest.value

        if not "host" in data:
            return {"error": "The host is not set."}, HttpCode.BadRequest.value

        host_id, result_code = self.create_host(
            data["user_id"], data["user_sign"], data["host"]
        )
        if result_code == StatusCode.Success:
            return {
                "host_id": host_id,
                "msg": f"Host has been successfully created.",
            }, HttpCode.Ok.value

        return {
            "error": "Unknown error. See the logs..."
        }, HttpCode.InternalServerError.value

    def __deauth(self):
        if not self._is_enable_net:
            return {
                "error": "Network module is disabled."
            }, HttpCode.ServiceUnvaliable.value

        data = request.get_json()
        if not "user_id" in data or not "user_sign" in data:
            return {
                "error": "The user parameters is not sets."
            }, HttpCode.BadRequest.value

        result_code = self.delete_user(data["user_id"], data["user_sign"])
        if result_code == StatusCode.Success:
            return {"msg": "User has been successfully deleted."}, HttpCode.Ok.value

        return {
            "error": "Unknown error. See the logs..."
        }, HttpCode.InternalServerError.value

    def __auth(self):
        if not self._is_enable_net:
            return {
                "error": "Network module is disabled."
            }, HttpCode.ServiceUnvaliable.value

        data = request.get_json()
        if not "permissions" in data:
            return {
                "error": "The permissions parameter is not set."
            }, HttpCode.BadRequest.value

        if (
            not "hostManagement" in data["permissions"]
            or not "botManagement" in data["permissions"]
            or not "databaseView" in data["permissions"]
        ):
            return {
                "error": "The arguments of the permissions parameter are set incorrectly."
            }, HttpCode.BadRequest.value

        user_info, result_code = self.add_user(
            permissions=Permissions(
                data["permissions"]["hostManagement"],
                data["permissions"]["botManagement"],
                data["permissions"]["databaseView"],
            )
        )

        if result_code == StatusCode.Success:
            return user_info, HttpCode.Ok.value

        return {
            "error": "Unknown error. See the logs..."
        }, HttpCode.InternalServerError.value

    def __switch_net(self, signum, frame):
        self._is_enable_net = not self._is_enable_net
        self.plog(
            f"Network module has been switched to: {self._is_enable_net}",
            StatusCode.Success,
        )

    def __stop(self, signum, frame):
        self._is_run = False
        self.stop_updater()
        self.plog("Stop signal", StatusCode.StopSignal)

    def __run_socket(self):
        self._app.run(host=self._host, port=self._port, debug=self._is_debug)

    def run(self):
        if not self._is_init:
            return

        self._socket_thread.start()

        self.plog("running....", StatusCode.Success)
        while self._is_run:
            # self.plog('some log')
            time.sleep(1)

        self.plog("stopped....", StatusCode.Success)


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="platform/platform-config.json",
        help="path to platform-config.json",
    )

    return parser.parse_args()


if __name__ == "__main__":
    opt = parse_opt()
    Platform(opt).run()
