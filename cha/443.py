from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import eval_js, go_app
from pywebio.session import info as sif
from pywebio.session import local, run_async
from pywebio.session import run_asyncio_coroutine as rac
from pywebio.session import run_js
from pywebio.platform.fastapi import webio_routes
from cha import index as cha
from fastapi import FastAPI
from uvicorn import Config, Server
import asyncio


app = FastAPI()
app.mount('/cha', FastAPI(routes=webio_routes(cha)))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    config = Config(app, loop=loop, port=80)
    config = Config(app, loop=loop, port=443, host='0.0.0.0', ssl_keyfile='api/8032637_api.drelf.cn.key', ssl_certfile='api/8032637_api.drelf.cn.pem')
    server = Server(config=config)
    loop.run_until_complete(server.serve())
