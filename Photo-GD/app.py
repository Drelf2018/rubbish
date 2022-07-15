from pywebio import start_server
from pywebio.input import file_upload, textarea
from pywebio.output import put_html, put_image, put_table, clear
from PIL import Image
from copy import copy


def dF(F, x: float, B: float, h: float = 10**-5) -> float:
    y = F(x, B)
    mid = 1 if abs(y) <= 10**-8 else 0
    while abs(y-mid) > 10**-8:
        h /= 10
        mid = (F(x, B+h) + F(x, B-h)) / 2
    return (F(x, B+h) - y) / h


class GD:
    def __init__(self, Data, F):
        self.G = lambda B: 1/len(Data)*sum([2*dF(F, x, B)*(F(x, B)-y) for x, y in Data])

    def run(self, B: float, v: float = 0.0, alpha: float = 0.01, rate: float = 0.01, limit: float = 10**-6) -> float:
        count = 0
        while (abs(g := self.G(B)) > limit) and (count < 10**6):
            count += 1
            if count % 10000 == 0:
                # print(g, B)
                ...
            v = alpha * v - rate * g
            B = B + v
        return int(B)


class Mode:
    变暗 = lambda A, B: min(A, B)
    变亮 = lambda A, B: max(A, B)
    正片叠底 = lambda A, B: A * B / 255
    滤色 = lambda A, B: 255 - (255-A) * (255-B) / 255
    颜色加深 = lambda A, B: A - (255-A) * (255-B) / B
    颜色减淡 = lambda A, B: A + A * B / (255-B)
    线性加深 = lambda A, B: A + B - 255
    线性减淡 = lambda A, B: A + B
    叠加 = lambda A, B: A * B / 128 if A <= 128 else 255 - (255-A) * (255-B) / 128
    强光 = lambda A, B: A * B / 128 if B <= 128 else 255 - (255-A) * (255-B) / 128
    柔光 = lambda A, B: A * B / 128 + (A/255)**2 * (255-2*B) if B <= 128 else A * (255-B) / 128 + (A/255)**0.5 * (2*B-255)
    亮光 = lambda A, B: A - (255-A) * (255-2*B) / (2*B) if B <= 128 else A + A * (2*B-255) / (2*(255-B))
    点光 = lambda A, B: min(A, 2*B) if B <= 128 else min(A, 2*B-255)
    线性光 = lambda A, B: A + 2*B - 255
    排除 = lambda A, B: A + B - A * B / 128
    差值 = lambda A, B: abs(A-B)
    # 相加 = lambda A, B: 
    # 减去 = lambda A, B: 


def main():
    '混合模式'
    file = file_upload('选择图片')
    with open(file['filename'], 'wb') as fp:
        fp.write(file['content'])
    image = Image.open(file['filename'])
    image = image.resize((int(150*image.width/image.height), 150))
    colors = ''
    while True:
        colors: str = textarea('输入修改颜色，用空格分隔修改前后颜色，换行输入多组数据', value=colors)
        try:
            Rd, Gd, Bd = [], [], []
            for color in colors.split('\n'):
                Rd.append([])
                Gd.append([])
                Bd.append([])
                for c in color.split(' '):
                    if c.replace('#', '').isalpha():
                        c = c.replace('#', '')
                        Rd[-1].append(int(c[:2], 16))
                        Gd[-1].append(int(c[2:4], 16))
                        Bd[-1].append(int(c[4:], 16))
                    else:
                        r, g, b = c.split(',')
                        Rd[-1].append(int(r))
                        Gd[-1].append(int(g))
                        Bd[-1].append(int(b))
        except Exception:
            continue

        tables = [[put_image(image, format='png'), put_html(f'<font size="6">原图</font>')]]
        for key, value in Mode.__dict__.items():
            if '__' in key:
                continue
            print(key, end=' ')
            R = GD(Rd, value).run(100)
            print(R, end=' ')
            G = GD(Gd, value).run(100)
            print(G, end=' ')
            B = GD(Bd, value).run(100)
            print(B, end=' ')
            if 0<=R<=255 and 0<=G<=255 and 0<=B<=255:
                color_code = f'#{hex(256*256*R+256*G+B)[2:].upper()}'
                print(color_code)
                img = copy(image)
                img = img.resize((int(150*img.width/img.height), 150))
                pim = img.load()
                for i in range(img.width):
                    for j in range(img.height):
                        color = list(pim[i, j])
                        for pos, b in enumerate([R, G, B]):
                            color[pos] = int(value(color[pos], b))
                        pim[i, j] = tuple(color)
                tables.append([
                    put_image(img, format='png'),
                    put_html(f'<font size="6" color="{color_code}">{key}■{color_code}</font>'),
                ])
            else:
                print('不合规')
        clear()
        put_table(tables, ['图片', '说明'])


if __name__ == '__main__':
    start_server(main, port=80, debug=True, auto_open_webbrowser=True)