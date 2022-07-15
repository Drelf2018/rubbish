import asyncio
import json

from cqBot import cqBot

cqbot = cqBot(debug=True)


async def read_config():
    while not cqbot.converse:
        await asyncio.sleep(1)

    with open('titles.json', 'r', encoding='utf-8') as fp:
        data = json.load(fp)

    for user_id, title in data['titles'].items():
        await cqbot.set_group_special_title(data['group_id'], user_id, title)

    await asyncio.sleep(5)
    cqbot.converse = None


asyncio.run(asyncio.wait([cqbot.run(), read_config()]))
