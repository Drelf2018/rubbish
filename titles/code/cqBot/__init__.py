import asyncio
import json
import logging

from aiowebsocket.converses import AioWebSocket

from .event import Mate, Message, get_event_from_msg


class cqBot():
    logger = logging.getLogger('cqBot')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[cqBot] [%(asctime)s] [%(levelname)s]: %(message)s", '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(handler)

    def __init__(self, url: str = 'ws://127.0.0.1:6700', debug=False):
        self.url = url
        self.converse = None
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    async def connect(self):
        while not self.converse:
            try:
                async with AioWebSocket(self.url) as aws:
                    self.converse = aws.manipulator
            except Exception:
                self.logger.debug('重连中...')
                await asyncio.sleep(3)
        return self.converse.receive

    async def run(self):
        recv = await self.connect()
        while self.converse:
            mes = await recv()
            # self.logger.debug(f'收到信息：{mes.decode("utf-8").strip()}')
            event = get_event_from_msg(mes)
            if isinstance(event, Mate):
                if event.event_type == 'lifecycle' and event.sub_type == 'connect':
                    self.logger.info('连接成功')
                elif event.event_type == 'heartbeat':
                    self.logger.debug('心跳中，将在 '+str(event.interval/1000)+' 秒后下次心跳 ')
            elif isinstance(event, Message):
                self.logger.info(f'收到信息：{event}')

    async def send(self, cmd):
        if isinstance(cmd, str):
            await self.converse.send(cmd)
        else:
            try:
                js = json.dumps(cmd, ensure_ascii=False)
                await self.converse.send(js)
            except Exception as e:
                self.logger.error('发送失败 '+str(e))

    async def set_group_special_title(self, group_id, user_id, title):
        await self.send({
            'action': 'set_group_special_title',
            'params': {
                'group_id': int(group_id),
                'user_id': int(user_id),
                'special_title': title,
                'duration': -1
            }
        })
