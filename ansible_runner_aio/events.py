import asyncio
import os
import json
import logging
import threading

logger = logging.getLogger('ansible-runner.zeromq')


class RunnerClientProtocol(asyncio.Protocol):

    def __init__(self, loop):
        self.transport = None

    def connection_made(self, transport):
        print("In connection made")
        super().connection_made(transport)
        self.transport = transport
        print("Connection to {}".format(transport.get_extra_info('peername')))

    def connection_lost(self, exc):
        print('Connection lost with the server...')


class RunnerServiceHandler:

    def __init__(self):
        self.host = None
        self.port = None
        self.loop = asyncio.new_event_loop()
        self.client_protocol = None

    async def send_data_actual(self, message):
        while True:
            if self.client_protocol is None or self.client_protocol.transport is None:
                await asyncio.sleep(1)
            else:
                return await self.client_protocol.transport.write(json.dumps(message).encode())

    async def send_hangup_actual(self):
        return await self.loop.stop()

    def send_data(self, message):
        return asyncio.run_coroutine_threadsafe(self.send_data_actual(message),
                                                self.loop)

    def send_hangup(self):
        return asyncio.run_coroutine_threadsafe(self.send_hangup_actual(),
                                                self.loop)

    def mainloop(self):
        asyncio.set_event_loop(self.loop)
        self.client_protocol = RunnerClientProtocol(self.loop)
        self.loop.create_task(self.loop.create_connection(lambda: self.client_protocol,
                                                          self.host,
                                                          self.port))
        self.loop.run_forever()


runner_service = RunnerServiceHandler()
service_thread = None


def set_configuration(runner_config):
    global service_thread
    runner_host = runner_config.settings.get("runner_service_host", None)
    runner_host = os.getenv("RUNNER_SERVICE_HOST", runner_host)
    runner_port = runner_config.settings.get("runner_service_port", None)
    runner_port = os.getenv("RUNNER_SERVICE_PORT", runner_port)
    if runner_host is None or runner_port is None:
        print("Runner AIO Plugin Skipped")
        return False
    if service_thread is None:
        runner_service.host = runner_host
        runner_service.port = runner_port
        service_thread = threading.Thread(target=runner_service.mainloop)
        service_thread.start()


def status_handler(runner_config, data):
    set_configuration(runner_config)
    runner_service.send_data(data)
    if 'status' in data and data['status'] in ('canceled', 'successful', 'timeout', 'failed'):
        runner_service.send_hangup()


def event_handler(runner_config, data):
    set_configuration(runner_config)
    runner_service.send_data(data)
