import os
import logging
import asyncio
import datetime

from weibo import Weibo
from d2p import create_new_img
from bilibili_api import Credential, dynamic
from apscheduler.schedulers.asyncio import AsyncIOScheduler


# b站cookies 根据账号自行填写
account = {
    'sessdata': '',
    'bili_jct': '',
    'buvid3': ''
}

# weibo.cn cookies
COOKIES = ''

logger = logging.getLogger('weibo_detector')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[Weibo][%(asctime)s][%(levelname)s]: %(message)s"))
logger.addHandler(handler)


def run(sched, uids, cookies):
    for i in range(len(uids)):
        @sched.scheduled_job('interval', seconds=30, next_run_time=datetime.datetime.now()+datetime.timedelta(seconds=10*i), args=[uids[i]])
        async def spider(uid):
            logger.info(f'正在更新用户 {uid} 微博')
            wb = Weibo(uid, cookies)
            headers = wb.get_headers()
            for i in range(1, 4):
                # 爬取前3条
                post = wb.get_post(i)
                pic_path = './pic/'+post['Mid']+'.png'
                if not os.path.exists(pic_path):
                    # 如果不存在就生成图片并发送动态
                    logger.info(f'用户 {uid} 微博 {post["Mid"]} 搬运中')
                    userInfo = wb.get_user_info()

                    # 保存图片
                    image = create_new_img(userInfo, post, headers)
                    image.save(pic_path, 'png')

                    await dynamic.send_dynamic('#脆鲨速报# 自动搬运[脸红]', images_path=[pic_path], credential=Credential(**account))
                else:
                    logger.info(f'用户 {uid} 微博 {post["Mid"]} 已存在')


sched = AsyncIOScheduler()
run(sched, [7198559139, 2203177060], COOKIES)
sched.start()
asyncio.get_event_loop().run_forever()
