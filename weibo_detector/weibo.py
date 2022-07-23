import re
import requests
from lxml import etree


# weibo.cn访问头 根据账号自行填写
headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
}


class Weibo():
    """
    weibo.cn 爬虫
    Args:
        uid (list) : 博主用户uid
        cookies (str) : 用户cookies
    """

    def __init__(self, uid, cookies):
        try:
            self.uid = int(uid)
            self.url = 'https://weibo.cn/u/'+str(uid)
        except Exception:
            self.url = 'https://weibo.cn/n/'+uid
        headers.update({'cookie': cookies})
        self.resp = None
        self.data = None
        self.comt = []
        self.update()

    def get_headers(self):
        return headers

    def update(self):
        # 刷新检测
        if not self.url:
            raise Exception('URL is Empty')
        else:
            try:
                self.resp = requests.get(self.url, headers=headers)
            except Exception as e:
                raise e
            self.data = etree.HTML(self.resp.text.encode('utf-8'))

    def get_user_info(self):
        # 获取博主当前信息
        resp = requests.get('https://m.weibo.cn/api/container/getIndex?type=uid&value=%d' % self.uid, headers=headers)
        data = resp.json()['data']['userInfo']
        info = {
            'name': data['screen_name'],  # 昵称
            'face': data['toolbar_menus'][0]['userInfo']['avatar_hd'],  # 头像
            'desc': data['description'],  # 个性签名
            'foll': data['follow_count'],  # 关注数(str)
            'foer': data['followers_count']  # 粉丝数(str)
        }
        return info

    def get_post(self, n: int):
        """
        爬取指定位置博文
        Args:
            n (int) : 正数第 n 条博文 /*包含置顶博文*/

        Returns:
            博文信息
        """

        if self.data is None:
            raise Exception('Update First')
        try:
            post = self.data.xpath('//div[@class="c"][{}]'.format(n))[0]
        except Exception as e:
            raise Exception('Error happened when n = %d %s' % (n, e))

        info = {
            'Top': 1 if post.xpath('.//span[@class="kt"]') else 0,  # 是否是置顶
            'Mid': post.xpath('.//@id')[0][2:],  # 这条博文的 mid 每条博文独一无二
            'repo': ''.join(post.xpath('./div/span[@class="cmt" and contains(text(), "转发理由:")]/../text()')).replace('\xa0', '')
        }

        def get_content_text(span):
            text = etree.tostring(span, encoding='utf-8').decode('utf-8')
            for _img in span.xpath('./span[@class="url-icon"]/img'):
                alt, src = _img.xpath('./@alt')[0], _img.xpath('./@src')[0]
                text = text.replace(
                    f'<span class="url-icon"><img alt="{alt}" src="{src}" style="width:1em; height:1em;" /></span>',
                    alt
                )
            for _a in span.xpath('.//a'):
                href = _a.xpath('./@href')[0].replace('&', '&amp;')
                atext = _a.xpath('./text()')[0]
                text = text.replace(f'<a href="{href}">{atext}</a>', atext)
            text = text.replace('<br />', '\n').replace('<span class="ctt">', '').replace('</span>', '')
            dot = len(text)
            for i in range(dot, 0, -1):
                if not text[i-1] == ' ':
                    dot = i
                    break
            return text[:dot]

        # 博文过长 更换网址进行爬取
        murl = post.xpath('.//a[contains(text(), "全文")]/@href')
        if murl:
            resp = requests.get('https://weibo.cn'+murl[0], headers=headers)
            data = etree.HTML(resp.text.encode('utf-8'))
            span = data.xpath('//div[@class="c" and @id="M_"]/div/span')[0]
            info['text'] = get_content_text(span)[1:]
            if info['repo']:
                info['text'] = f'转发了 {span.xpath("../a/text()")[0]} 的微博：\n' + info['text']
        else:
            span = post.xpath('./div/span[@class="ctt"]')[0]
            info['text'] = get_content_text(span)
            if info['repo']:
                info['text'] = ''.join(span.xpath('../span[@class="cmt"][1]//text()')) + '\n' + info['text']

        # 爬取博文中图片
        pics = re.findall(r'组图共\d张', '/'.join(post.xpath('.//text()')))
        if pics:
            info['text'] = info['text'][:-1]
            turl = post.xpath(f'.//a[contains(text(), "{pics[0]}")]/@href')[0]
            resp = requests.get(turl, headers=headers)
            data = etree.HTML(resp.text.encode('utf-8'))
            info['PicAll'] = [('https://weibo.cn/' + url) for url in data.xpath('.//a[contains(text(), "原图")]/@href')]
        else:
            opic = post.xpath('.//a[contains(text(), "原图")]/@href')
            if opic:
                info['PicOri'] = opic[0]

        # 将其他信息与博文正文分割
        info['Time'] = post.xpath('./div/span[@class="ct"]/text()')[0]

        return info

    def comment(self, mid, count):
        # 未使用 爬取评论的
        self.comt = []
        total = 0
        url = 'https://weibo.cn/comment/' + mid
        params = {'page': 1}
        while total < count or count < 0:
            resp = requests.get(url, headers=headers, params=params)
            data = etree.HTML(resp.text.encode('utf-8'))
            comts = data.xpath('//div[@class="c" and @id and not(@id="M_")]')
            for comt in comts:
                for a in comt.xpath('./span[@class="ctt"]/a'):
                    href = a.xpath("./@href")[0]
                    if re.search(r'[a-zA-z]+://[^\s]*', href):
                        self.comt.append(href)
                total += 1
            params['page'] += 1
