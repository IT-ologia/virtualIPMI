#!/usr/bin/env python3.8

# Copyright (C) 2020 IT-ologia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import subprocess
import logging

from typing import Dict

from pyghmi.ipmi.private.session import Session as IpmiSession
from pyghmi.ipmi.private.serversession import IpmiServer as BaseIpmiServer
from pyghmi.ipmi.private.serversession import ServerSession as IpmiServerSession


_logger = logging.getLogger("virtualIPMI")


class _BmcServer(BaseIpmiServer):  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        user: str,
        password: str,
        listen_host: str,
        listen_port: int,
        listen_timeout: float,

        managed_host: str,
        process_timeout: float,

        power_action_path: str,
        power_status_path: str,
        chassis_bootdev_path: str,
        chassis_bootparam_get_path: str,
    ) -> None:

        super().__init__(authdata={user: password}, address=listen_host, port=listen_port)

        self.__listen_host = listen_host
        self.__listen_port = listen_port
        self.__listen_timeout = listen_timeout

        self.__managed_host = managed_host
        self.__process_timeout = process_timeout

        self.__power_action_path = power_action_path
        self.__power_status_path = power_status_path
        self.__chassis_bootdev_path = chassis_bootdev_path
        self.__chassis_bootparam_get_path = chassis_bootparam_get_path

    def run(self) -> None:
        _logger.info("Listening IPMI on [%s]:%d ...", self.__listen_host, self.__listen_port)
        try:
            while True:
                IpmiSession.wait_for_rsp(self.__listen_timeout)
        except (SystemExit, KeyboardInterrupt):
            pass
        _logger.info("Good bye")

    def handle_raw_request(self, request: Dict, session: IpmiServerSession) -> None:
        handler = {
            (6, 1): (lambda _, __, session: self.send_device_id(session)),  # Get device ID
            (0, 1): self.__get_power_status_handler,  # Get chassis status
            (0, 2): self.__set_power_status_handler,  # Chassis control
            (0, 9): self.__get_boot_device,  # Chassis bootparam get 5
            (0, 8): self.__set_boot_device,  # Chassis bootdev <xxx>
        }.get((request["netfn"], request["command"]))

        if handler is not None:
            client: str = session.sockaddr[0]
            try:
                handler(client, request, session)
            except Exception:
                _logger.exception("%s: Unexpected exception while handling IPMI request: netfn=%d; command=%d",
                                  client, request["netfn"], request["command"])
                session.send_ipmi_response(code=0xFF)
        else:
            session.send_ipmi_response(code=0xC1)

    def __get_power_status_handler(self, client: str, _: Dict, session: IpmiServerSession) -> None:
        _logger.info("%s: Power status", client)
        status = self.__run_process(self.__power_status_path, self.__managed_host).lower()
        if status not in ["on", "off"]:
            raise RuntimeError(f"{client}: Got unsupported power status from the process: {status!r}")
        session.send_ipmi_response(data=[int(status == "on"), 0, 0])

    def __set_power_status_handler(self, client: str, request: Dict, session: IpmiServerSession) -> None:
        action = {
            0: "off",
            1: "on",
            2: "cycle",
            3: "reset",
            4: "diag",
            5: "soft",
        }.get(request["data"][0], "")
        if not action:
            raise RuntimeError(f"{client}: Received unknown IPMI chassis control request: {request['data'][0]!r}")
        _logger.info("%s: Power %s", client, action)
        self.__run_process(self.__power_action_path, self.__managed_host, action)
        session.send_ipmi_response(code=0)

    def __get_boot_device(self, client: str, request: Dict, session: IpmiServerSession) -> None:
        if request["data"][0] == 5:  # Boot flags
            _logger.info("%s: Chassis bootparam get 5", client)
            device = self.__run_process(self.__chassis_bootparam_get_path, self.__managed_host, "5")
            code = {
                "pxe": 4,
                "cdrom": 0x14,
                "disk": 8,
            }.get(device)
            if code is None:
                raise RuntimeError(f"{client}: Got unsupported boot from the process: {device!r}")
            session.send_ipmi_response(data=[1, 5, 0b10000000, code, 0, 0, 0])
        else:
            session.send_ipmi_response(code=0x80)

    def __set_boot_device(self, client: str, request: Dict, session: IpmiServerSession) -> None:
        if request["data"][0] in [0, 3, 4]:
            session.send_ipmi_response()
        elif request["data"][0] == 5:
            code = (request["data"][2] >> 2) & 0b1111
            device = {
                1: "pxe",
                5: "cdrom",
                2: "disk",
            }.get(code)
            if device is None:
                session.send_ipmi_response(code=0xCC)
                return
            _logger.info("%s: Chassis bootdevice %s", client, device)
            self.__run_process(self.__chassis_bootdev_path, self.__managed_host, device)
            session.send_ipmi_response()
        else:
            session.send_ipmi_response(code=0xC1)

    def __run_process(self, *cmd: str) -> str:
        assert len(cmd) >= 1
        proc = subprocess.run(cmd, capture_output=True, check=False, timeout=self.__process_timeout)
        for line in proc.stderr.decode(errors="ignore").split("\n"):
            if (line := line.rstrip()):
                _logger.info(" ... %s: %s", cmd[0], line)
        if proc.returncode != 0:
            raise RuntimeError(f"Process error; returncode={proc.returncode!r}")
        return proc.stdout.decode(errors="ignore").strip()


def _getenv_not_empty(name: str, default: str) -> str:
    value = os.getenv(name, default)
    if not value:
        raise RuntimeError(f"Empty variable ${name}")
    return value


def _getenv_exec_path(name: str, default: str) -> str:
    path = _getenv_not_empty(name, default)
    if not os.path.isfile(path) or not os.access(path, os.X_OK):
        raise RuntimeError("Non-executable path in variable ${name}")
    return path


def main() -> None:
    log_path = (os.getenv("IPMI_LOG_FILE", "") or None)
    logging.basicConfig(
        format="%(asctime)s %(levelname)s --- %(message)s",
        level=_getenv_not_empty("IPMI_LOG_LEVEL", "INFO").upper(),
        filename=log_path,
    )
    if log_path:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s --- %(message)s"))
        logging.getLogger("").addHandler(console_handler)

    _BmcServer(
        user=_getenv_not_empty("IPMI_USER", "admin"),
        password=_getenv_not_empty("IPMI_PASSWORD", "admin"),
        listen_host=_getenv_not_empty("IPMI_LISTEN_HOST", "0.0.0.0"),
        listen_port=int(_getenv_not_empty("IPMI_LISTEN_PORT", "623")),
        listen_timeout=float(_getenv_not_empty("IPMI_LISTEN_TIMEOUT", "10.0")),

        managed_host=_getenv_not_empty("IPMI_MANAGED_HOST", "localhost"),
        process_timeout=float(_getenv_not_empty("IPMI_PROCESS_TIMEOUT", "10.0")),

        power_action_path=_getenv_exec_path("IPMI_POWER_ACTION", "/root/scripts/power-action.sh"),
        power_status_path=_getenv_exec_path("IPMI_POWER_STATUS", "/root/scripts/power-status.sh"),
        chassis_bootdev_path=_getenv_exec_path("IPMI_CHASSIS_BOOTDEV", "/root/scripts/chassis-bootdev.sh"),
        chassis_bootparam_get_path=_getenv_exec_path("IPMI_CHASSIS_BOOTPARAM_GET", "/root/scripts/chassis-bootparam-get.sh"),
    ).run()


if __name__ == "__main__":
    main()
