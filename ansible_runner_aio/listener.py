import asyncio
import logging

logger = logging.getLogger(__name__)


class RunnerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print("Connection from {}".format(peername))

    def data_received(self, data):
        print(data)


def listen():
    loop = asyncio.get_event_loop()
    listener = loop.create_server(
        RunnerProtocol, '127.0.0.1', 8888)
    loop.create_task(listener)
    print("Serving on {}:{}".format('127.0.0.1', 8888))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()
