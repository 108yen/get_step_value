import tkinter
import time
import threading
import pandas as pd
from datetime import datetime, timedelta

"""
ファイルを読み込んでcanvasにチャートを描画
canvas: tkinter.Canvas
code:   string
date:   string
candle_width    int
"""
class UpdateCanvas(threading.Thread):
    def __init__(self, canvas, code, date, candle_width):
        super(UpdateCanvas, self).__init__()
        self.canvas = canvas
        self.code=code
        self.date=date
        self.candle_width=candle_width
        self.stop_event = threading.Event()
        self.setDaemon(True)

    def stop(self):
        self.stop_event.set()

    def run(self):
        # 午前ぶん
        fname = self.code+'_'+self.date+'_1130.csv'
        input_fname = 'data/'+fname
        am_data = pd.read_csv(input_fname, header=0, index_col=0,
                            encoding='cp932').iloc[::-1]
        # 午後ぶん
        fname = self.code+'_'+self.date+'_1500.csv'
        input_fname = 'data/'+fname
        pm_data = pd.read_csv(input_fname, header=0, index_col=0,
                            encoding='cp932').iloc[::-1]
        pm_data = pm_data[pm_data['時刻'] > "11:30:00"]
        row_df = pd.concat([am_data, pm_data])
        ini_val = int(row_df[:1]['約定値'].values[0])
        defy = 200  # y軸の基準の位置
        recsy = 200  # その足のスタートの位置
        max = 0
        min = 0
        minutes_num = 0
        # 出来高表示のための変数
        buy_col = '#cd5c5c'
        sell_col = '#4169e1'
        vol_mag = 1200  # 倍率　これで割られる
        buy_volume = 0  # 出来高
        sell_volume = 0
        pre_value = 0  # 前の価格
        buy_dir = True  # 買いか売りか 初めは本当は前日と比較する必要あり
        split5m = datetime.strptime("09:05:00", '%H:%M:%S')
        ini_time = datetime.strptime(row_df[:1]['時刻'].values[0], '%H:%M:%S').time()
        while ini_time > split5m.time():
            split5m = split5m+timedelta(minutes=5)

        self.canvas.create_line(15, 450, 15, 450, width=5,
                        fill=buy_col, tag='buy_volume0')
        self.canvas.create_line(15, 450, 15, 450, width=5,
                        fill=sell_col, tag='sell_volume0')
        self.canvas.create_line(0, 450-150, 800, 450-150)
        # 2%と4%の線
        self.canvas.create_line(0, defy, self.canvas.winfo_width(),
                        defy, width=1, fill='#3cb371', tag='two_per')
        self.canvas.create_line(0, defy, self.canvas.winfo_width(),
                        defy, width=1, fill='#ffa07a', tag='four_per')
        # ローソク足
        self.canvas.create_line(10+self.candle_width//2, defy, 10 +
                                self.candle_width//2, defy, tag='line0')
        self.canvas.create_rectangle(10, defy, 10+self.candle_width,
                                defy, fill='red', tag='rect0')
        # 価格表示
        self.canvas.create_text(60, defy, text='', tag='value')

        for index, data in row_df.iterrows():
            if self.stop_event.is_set():
                print('stop')
                break
            time.sleep(0.01)
            contract_price = int(data['約定値'])
            gap = contract_price-ini_val
            sx = 10 + (3+self.candle_width)*minutes_num
            sy = recsy
            fx = sx+self.candle_width
            fy = defy-gap
            linex = sx+self.candle_width//2
            # 2%と4%の線の処理
            two_per_y = int(defy-(contract_price*1.02-ini_val))
            four_per_y = int(defy-(contract_price*1.04-ini_val))
            self.canvas.coords('two_per', 10, two_per_y, 790, two_per_y)
            self.canvas.coords('four_per', 10, four_per_y, 790, four_per_y)

            # 出来高表示の処理
            if pre_value < contract_price:
                buy_dir = True
            elif pre_value > contract_price:
                buy_dir = False
            pre_value = contract_price
            if buy_dir:
                buy_volume += int(data['出来高'])
            else:
                sell_volume += int(data['出来高'])
            # 5分足を分けるための処理
            if split5m.time() <= datetime.strptime(data['時刻'], '%H:%M:%S').time():
                while datetime.strptime(data['時刻'], '%H:%M:%S').time() >= split5m.time():
                    split5m = split5m+timedelta(minutes=5)
                print(split5m)
                minutes_num += 1
                recsy = defy-gap
                max = gap
                min = gap
                sx = 10 + (3+self.candle_width)*minutes_num
                sy = recsy
                fx = sx+self.candle_width
                fy = defy-gap
                linex = sx+self.candle_width//2
                # 出来高表示処理
                if buy_dir:
                    buy_volume = int(data['出来高'])
                    sell_volume = 0
                else:
                    buy_volume = 0
                    sell_volume = int(data['出来高'])
                sell_sy = 450
                sell_fy = sell_sy-sell_volume//vol_mag
                buy_sy = sell_fy
                buy_fy = buy_sy-buy_volume//vol_mag
                self.canvas.create_line(linex, buy_sy, linex, buy_fy, width=5, fill=buy_col,
                                tag='buy_volume'+str(minutes_num))
                self.canvas.create_line(linex, sell_sy, linex, sell_fy, width=5, fill=sell_col,
                                tag='sell_volume'+str(minutes_num))
                # ローソク足
                self.canvas.create_line(linex, defy-max, linex,
                                defy - min, tag='line'+str(minutes_num))
                self.canvas.create_rectangle(
                    sx, sy, fx, fy, fill='red', tag='rect'+str(minutes_num))
            else:
                # 足
                self.canvas.coords('rect'+str(minutes_num), sx, sy, fx, fy)
                if recsy < fy:
                    self.canvas.itemconfig(
                        'rect'+str(minutes_num), fill='blue')
                else:
                    self.canvas.itemconfig('rect'+str(minutes_num), fill='red')
                # ヒゲ
                if gap > max:
                    max = gap
                if gap < min:
                    min = gap
                self.canvas.coords('line'+str(minutes_num), linex,
                            defy-max, linex, defy-min)
                # 出来高
                sell_sy = 450
                sell_fy = sell_sy-sell_volume//vol_mag
                buy_sy = sell_fy
                buy_fy = buy_sy-buy_volume//vol_mag
                self.canvas.coords('buy_volume'+str(minutes_num),
                            linex, buy_sy, linex, buy_fy)
                self.canvas.coords('sell_volume'+str(minutes_num),
                            linex, sell_sy, linex, sell_fy)
                # 出来高が長すぎる時の処理
                if sell_sy-buy_fy > 150:
                    vol_mag = int(vol_mag*1.1)
                    for i in range(minutes_num):
                        sell_sx, sell_sy, sell_fx, sell_fy = self.canvas.coords(
                            'sell_volume'+str(i))
                        buy_sx, buy_sy, buy_fx, buy_fy = self.canvas.coords(
                            'buy_volume'+str(i))
                        sell_ln = ((sell_sy-sell_fy)*10)//11
                        buy_ln = ((buy_sy-buy_fy)*10)//11
                        sell_fy = sell_sy-sell_ln
                        buy_sy = sell_fy
                        buy_fy = buy_sy-buy_ln
                        self.canvas.coords('sell_volume'+str(i), sell_sx,
                                    sell_sy, sell_fx, sell_fy)
                        self.canvas.coords('buy_volume'+str(i), buy_sx,
                                    buy_sy, buy_fx, buy_fy)
            # 価格の表示
            self.canvas.itemconfig('value', text=data['約定値'])
            self.canvas.coords('value', fx+40, fy)
            # チャートが上に激突しないようにする処理
            if four_per_y < 20:
                defy += 10
                recsy += 10
                for i in range(minutes_num):
                    self.canvas.move('line'+str(i), 0, 10)
                    self.canvas.move('rect'+str(i), 0, 10)
            # print(data['時刻'])
            # print(gap)


def main():
    print()


if __name__ == '__main__':
    main()
