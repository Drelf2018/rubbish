import asyncio
import sys
import time
import webbrowser
from functools import partial
from io import BytesIO

import aiohttp
from PIL import Image, ImageDraw
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import eval_js, run_async
from pywebio.session import run_asyncio_coroutine as rac
from pywebio.session import run_js


with open(__file__, 'r', encoding='utf-8') as fp:
    CODE = fp.read()
BASEURL = 'https://account.bilibili.com/api/member/getCardByMid?mid={}'
HEADERS = {
    'Connection': 'keep-alive',
    'content-type': 'text/plain; charset=utf-8',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
}
SORTED_LIST = []


async def exface(session: aiohttp.ClientSession, face: str, pendant: str) -> Image.Image:
    # 头像后处理
    if isinstance(face, str):
        response = await session.get(face)  # 请求图片
        face = Image.open(BytesIO(await response.read()))  # 读取图片
    w, h = face.size
    if not w == h:
        w, h = max(w, h), max(w, h)
        face = face.resize((w, h), Image.ANTIALIAS)  # 规范头像为正方形
    a = Image.new('L', face.size, 0)  # 创建一个黑色背景的画布
    ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色圆形
    
    # 装扮
    if pendant:
        image = Image.new('RGBA', (int(1.75*w), int(1.75*h)), (0, 0, 0, 0))
        image.paste(face, (int(0.375*w), int(0.375*h)), mask=a)  # 粘贴至背景
        response = await session.get(pendant)  # 请求图片
        pd = Image.open(BytesIO(await response.read()))  # 读取图片
        pd = pd.resize((int(1.75*w), int(1.75*h)), Image.ANTIALIAS)  # 装扮应当是头像的1.75倍
        try:
            r, g, b, a = pd.split()  # 分离alpha通道
            image.paste(pd, (0, 0), mask=a)  # 粘贴至背景
            return image
        except Exception:
            pendant = None

    # 粉圈
    if not pendant:
        image = Image.new('RGBA', (int(1.16*w), int(1.16*h)), (0, 0, 0, 0))
        image.paste(face, (int(0.08*w), int(0.08*h)), mask=a)  # 粘贴至背景
        ps = Image.new("RGB", (int(1.16*w), int(1.16*h)), (242, 93, 142))
        a = Image.new('L', ps.size, 0)  # 创建一个黑色背景的画布
        ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色外圆
        ImageDraw.Draw(a).ellipse((int(0.06*w), int(0.06*h), int(1.1*w), int(1.1*h)), fill=0)  # 画黑色内圆
        image.paste(ps, (0, 0), mask=a)  # 粘贴至背景
        w, h = image.size
        bg = Image.new('RGBA', (int(1.25*w), int(1.25*h)), (0, 0, 0, 0))
        bg.paste(image, (int((1.25-1)/2*w), int((1.25-1)/2*h)))
        return bg


async def get_uid(session: aiohttp.ClientSession, id: int, uid: int) -> dict:
    flag = False
    try:
        resp = await session.get(BASEURL.format(uid))
        print((await resp.read()).decode('utf-8'))    
        js = await resp.json(content_type=None, encoding='utf-8')
    except Exception as e:
        print(e)
        flag = True
        session = aiohttp.ClientSession(headers=HEADERS)
        resp = await session.get(BASEURL.format(uid))
        js = await resp.json(content_type=None, encoding='utf-8')

    info = js['card']
    image = await exface(session, info.get('face'), info.get('pendant', {}).get('image'))
    if flag:
        await session.close()
    return {
        'id': id+1,
        'face': image,
        'name': info['name'],
        'uid': info['mid'],
        'attentions': info['attentions']
    }


def callback(p, key=int) -> int:
    left, mid, right = 0, 0, len(SORTED_LIST)
    uid = key(p)
    while left < right:
        mid = (left + right) // 2
        if key(SORTED_LIST[mid]) < uid:
            left = mid + 1
        else:
            right = mid
    else:
        mid = (left + right) // 2
    SORTED_LIST[mid:] = [p] + SORTED_LIST[mid:]
    return -1 if mid == len(SORTED_LIST) - 1 else mid, p


async def get_info(uids: list, content: str, scope: str, callback: "function" = callback):
    SORTED_LIST.clear()
    count = 0
    sum_count = len(uids)
    session = aiohttp.ClientSession(headers=HEADERS)
    pending = [asyncio.create_task(get_uid(session, id, uid)) for id, uid in enumerate(uids) if str(uid).isdigit()]

    st = time.time()
    while pending:
        done, pending = await rac(asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED))
        time_str = time.strftime('%H:%M:%S', time.localtime())
        put_markdown(f'`{time_str}` `DEBUG` pending: {len(pending)}', scope='background')
        for done_task in done:
            position, info = callback(await done_task, lambda p: p['id'])
            row = put_row([
                put_image(info['face'], format='png', height='100px'),
                put_column([
                    None,
                    put_markdown(content.format_map(info)).style('border-bottom: none'),
                    None
                ]),
                None
            ], size='auto auto 1fr', scope=scope, position=position)
            row.onclick(partial(run_js, code_=f'tw=window.open();tw.location="https://space.bilibili.com/{info["uid"]}";'))

            time_str = time.strftime('%H:%M:%S', time.localtime())
            put_markdown(f'`{time_str}` `INFO` 完成查找：{info["name"]}', scope='background')   
            count += 1
            set_processbar('bar', count / sum_count)
    sp = time.time()
    toast(f'用时: {round(sp-st, 2)} 秒', 3)
    await rac(session.close())


async def index():
    '怎么你也喜欢查关注吗'

    uids = await eval_js('prompt("查共同关注用英文逗号(,)连接多个uid")')

    put_tabs([
        {'title': '主页', 'content': put_scope('main')},
        {'title': '后台', 'content': put_scrollable(put_scope('background'), height=600, keep_bottom=True)},
        {'title': '源码', 'content': [
            put_html('<font size="6px"><b>😎你知道我长什么样 来找我吧</b></font>').onclick(partial(run_js, code_='''tempwindow=window.open();
                                                              tempwindow.location="https://github.com/Drelf2018";''')),
            put_code(CODE, 'python')]},
        {'title': '私货', 'content': put_html('''
            <iframe src="https://player.bilibili.com/player.html?aid=78090377&bvid=BV1vJ411B7ng&cid=133606284&page=1&high_quality=1" 
                width="100%" height="600" scrolling="true" border="0" frameborder="no" framespacing="0" allowfullscreen="true"> </iframe>
        ''')},
        {'title': '退出', 'content': [
            put_button('强制结束程序', color='danger', onclick=lambda: sys.exit(0)),
            put_markdown('__若不结束程序，将会在`后台`运行，可通过此网址多次使用__')
        ]}
    ]).style('border:none;')

    try:
        assert uids is not None and uids is not '', 'input error'
        task = run_async(get_info(uids.split(','), content='## 😚欢迎你呀，{name}🥳', scope='main'))
    except Exception:
        toast('输入不正确，请刷新页面重新输入', 0, color='error')
        return

    while not task.closed():
        await asyncio.sleep(0.33)

    info = SORTED_LIST

    if len(info) == 0:
        toast('输入不正确，请刷新页面重新输入', 0, color='error')
    else:
        if len(info) == 1:
            mids = info[0]['attentions']
            put_markdown(f'共查询到 `{len(mids)}` 个关注', scope='main')
        else:
            same = set(info[0]['attentions'])
            for u in info:
                same &= set(u['attentions'])
            mids = [mid for mid in info[0]['attentions'] if mid in same]
            put_markdown(f'共查询到 `{len(mids)}` 个共同关注', scope='main')

        put_processbar('bar', scope='main')

        put_tabs([
            {'title': '关注列表', 'content': put_scope('list')},
            {'title': '文字列表', 'content': [
                put_markdown(f'{nid}. `{uid}`').onclick(
                    partial(run_js, code_=f'tw=window.open();tw.location="https://space.bilibili.com/{uid}";'))
            for nid, uid in enumerate(mids, 1)]}
        ], scope='main').style('border:none;')
        
        run_async(get_info(mids, content='## `{id}` {name}', scope='list'))


if __name__ == '__main__':
    try:
        start_server(index, 2434, auto_open_webbrowser=True, debug=True)
    except Exception:
        webbrowser.open('http://localhost:2434')
