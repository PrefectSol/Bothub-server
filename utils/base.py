import os
import time
import json
import shutil
import threading
import hashlib
import secrets
import subprocess
from datetime import datetime

from utils.status import StatusCode
from utils.permissions import Permissions
from hub.hprocess_handler import HProcessHandler


class Base:
    def __init__(self, base_dir: str):
        self._secret_size = 16
        self._is_update = False

        self._users_dir = os.path.join(base_dir, "users/")
        self._platform_dir = os.path.join(base_dir, "platform/")
        self._hosts_dir = os.path.join(base_dir, "hosts/")

        if not os.path.exists(self._users_dir):
            os.mkdir(self._users_dir)

        if not os.path.exists(self._platform_dir):
            os.mkdir(self._platform_dir)

        if not os.path.exists(self._hosts_dir):
            os.mkdir(self._hosts_dir)

        self.__update_dates()

        self._update_thread = threading.Thread(target=self.__updater)
        self._hprocess_handler = HProcessHandler(self.hlog_to)

    def init_base(self, encoder, platform_file):
        self._encoder = encoder
        self._platform_file = platform_file

    def __update_dates(self):
        self._current_date = datetime.now()
        self._log_file = self._current_date.strftime("%Y-%m-%d_%H:%M:%S")

    def __updater(self):
        while self._is_update:
            elapsed_time = datetime.now() - self._current_date
            if elapsed_time.total_seconds() >= self._log_update * 3600:
                self.__update_dates()

            time.sleep(self._delay)

    def __check_user(self, user_id, user_sign, permissions=None) -> StatusCode:
        userfile = os.path.join(self._users_dir, f"user_{user_id}.env")
        if not os.path.isfile(userfile):
            return StatusCode.UnknownUser

        with open(userfile, "r") as file:
            data = file.read().split(" ")

        if data[0] != user_sign:
            return StatusCode.InvalidSignature

        if permissions != None:
            if not (
                int(data[1] == "True") >= int(permissions[0])
                and int(data[2] == "True") >= int(permissions[1])
                and int(data[3] == "True") >= int(permissions[2])
            ):
                return StatusCode.InvalidPermissions

        return StatusCode.Success

    def run_updater(self, log_update: float, delay: int):
        self._log_update = log_update
        self._delay = delay
        self._is_update = True
        self._update_thread.start()

    def stop_updater(self):
        self._is_update = False

    def is_view(self, user_id, user_sign) -> StatusCode:
        return self.__check_user(
            user_id=user_id, user_sign=user_sign, permissions=(False, False, True)
        )

    def post_bot(self, user_id, user_sign, bot_source, host_id) -> StatusCode:
        result = self.__check_user(
            user_id=user_id, user_sign=user_sign, permissions=(False, True, False)
        )
        if result != StatusCode.Success:
            return result

        return self._hprocess_handler.send_data(host_id, bot_source)

    def delete_host(self, user_id, user_sign, host_id) -> StatusCode:
        result = self.__check_user(
            user_id=user_id, user_sign=user_sign, permissions=(True, False, False)
        )
        if result != StatusCode.Success:
            return result

        with open(os.path.join(self._users_dir, f"user_{user_id}.env"), "r") as file:
            data = file.read().split(" ")

        hosts = data[4:]
        if host_id not in hosts:
            return StatusCode.HostNotFound

        self._hprocess_handler.delete(host_id)

        hosts.remove(host_id)
        with open(os.path.join(self._users_dir, f"user_{user_id}.env"), "w") as file:
            file.write(f"{data[0]} {data[1]} {data[2]} {data[3]}")
            for host in hosts:
                file.write(" " + host)

        shutil.rmtree(os.path.join(self._hosts_dir, f"host_{host_id}"))

        return StatusCode.Success

    def create_host(self, user_id, user_sign, host: dict) -> tuple[int, StatusCode]:
        result = self.__check_user(
            user_id=user_id, user_sign=user_sign, permissions=(True, False, False)
        )
        if result != StatusCode.Success:
            return -1, result

        dirs = [
            name
            for name in os.listdir(self._hosts_dir)
            if os.path.isdir(os.path.join(self._hosts_dir, name))
            and name.startswith("host_")
        ]
        numbers = [int(file.split("_")[1]) for file in dirs]
        host_id = str(min(set(range(1, len(numbers) + 2)) - set(numbers)))

        subprocess.check_output(["pip", "install"] + host["requirements"].split(" "))

        pid = self._hprocess_handler.create(
            host["game"], host["source"], host["settings"], host_id
        )

        host_dir = os.path.join(self._hosts_dir, f"host_{host_id}/")
        os.mkdir(host_dir)

        with open(os.path.join(host_dir, "owner.env"), "w") as file:
            file.write(user_id)

        with open(os.path.join(self._users_dir, f"user_{user_id}.env"), "a") as file:
            file.write(f" {host_id}")

        return host_id, StatusCode.Success

    def delete_user(self, user_id, user_sign) -> StatusCode:
        result = self.__check_user(user_id=user_id, user_sign=user_sign)
        if result != StatusCode.Success:
            return result

        userfile = os.path.join(self._users_dir, f"user_{user_id}.env")
        with open(userfile, "r") as file:
            data = file.read().split(" ")

        hosts = data[4:]
        for host in hosts:
            shutil.rmtree(os.path.join(self._hosts_dir, f"host_{host}"))

        os.remove(userfile)

        return StatusCode.Success

    def add_user(self, permissions: Permissions) -> tuple[dict, StatusCode]:
        files = [
            name
            for name in os.listdir(self._users_dir)
            if os.path.isfile(os.path.join(self._users_dir, name))
            and name.startswith("user_")
        ]
        numbers = [int(file.split("_")[1].split(".")[0]) for file in files]
        user_id = str(min(set(range(1, len(numbers) + 2)) - set(numbers)))

        user_secret = secrets.token_hex(self._secret_size)

        hash_object = hashlib.sha256()
        hash_object.update((user_id + user_secret).encode(self._encoder))
        secret_hash = hash_object.hexdigest()

        with open(self._users_dir + f"user_{user_id}.env", "w") as file:
            file.write(
                f"{secret_hash} {permissions.get_host_permission()} {permissions.get_bot_permission()} {permissions.get_view_permission()}"
            )

        return {"user_id": user_id, "user_secret": user_secret}, StatusCode.Success

    def plog(self, msg: str, status: StatusCode = StatusCode.Unknown):
        with open(
            os.path.join(self._platform_dir, self._log_file) + ".log", "a"
        ) as file:
            file.write(
                f"[{datetime.now()}] --- [{status.name}:{status.value}] --- {msg}\n"
            )

    def hlog_to(self, msg, target: str, status: StatusCode = StatusCode.Unknown):
        if isinstance(msg, dict):
            msg = json.dumps(msg, indent=4, ensure_ascii=False).replace("\\n", "\n")
        host_dir = os.path.join(self._hosts_dir, f"host_{target}/")
        with open(os.path.join(host_dir, self._log_file) + ".log", "a") as file:
            file.write(
                f"[{datetime.now()}] --- [{status.name}:{status.value}] --- {msg}\n"
            )
