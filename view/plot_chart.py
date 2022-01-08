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
    def __init__(self, canvas, code, date, candle_width, candle_rate, volume_rate, max_val, min_val, minutes_num):
        super(UpdateCanvas, self).__init__()
        self.canvas = canvas
        self.code = code
        self.date = date
        self.candle_width = candle_width
        self.candle_rate = candle_rate
        self.volume_rate = volume_rate
        self.max_val = max_val
        self.min_val = min_val
        self.minutes_num = minutes_num+1  # 次の足から描画するので
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
        # 始まりの値が前日の高値と低値の外だったら倍率も変える必要がある
        ini_val = int(row_df[:1]['約定値'].values[0])
        defy = 0
        # 範囲外だった場合倍率も変更する必要がある
        if self.min_val > ini_val or ini_val > self.max_val:
            pre_min_val = self.min_val
            if self.min_val > ini_val:
                self.min_val = ini_val
                self.min_id = self.minutes_num
            elif self.max_val < ini_val:
                self.max_val = ini_val
                self.max_id = self.minutes_num
            pre_candle_rate = self.candle_rate
            self.candle_rate = 300/(self.max_val-self.min_val)
            recal_past_chart(self.canvas, self.minutes_num, pre_candle_rate,
                 self.candle_rate, pre_min_val, self.min_val)
        # y軸の基準の位置 (初めの足の始まりの位置)
        defy = 300-int((ini_val-self.min_val)*self.candle_rate)
        recsy = defy  # その足のスタートの位置(初めはdefy)
        max = 0
        min = 0
        # 出来高表示のための変数
        buy_col = '#cd5c5c'
        sell_col = '#4169e1'
        buy_volume = 0  # 出来高
        sell_volume = 0
        pre_value = 0  # 前の価格
        buy_dir = True  # 買いか売りか 初めは本当は前日と比較する必要あり
        split5m = datetime.strptime("09:05:00", '%H:%M:%S')
        ini_time = datetime.strptime(
            row_df[:1]['時刻'].values[0], '%H:%M:%S').time()
        while ini_time >= split5m.time():
            split5m = split5m+timedelta(minutes=5)

        self.canvas.create_line(15, 450, 15, 450, width=5,
                                fill=buy_col, tag='buy_volume'+str(self.minutes_num))
        self.canvas.create_line(15, 450, 15, 450, width=5,
                                fill=sell_col, tag='sell_volume'+str(self.minutes_num))
        # 2%と4%の線
        self.canvas.create_line(0, defy, self.canvas.winfo_width(),
                                defy, width=1, fill='#3cb371', tag='two_per')
        self.canvas.create_line(0, defy, self.canvas.winfo_width(),
                                defy, width=1, fill='#ffa07a', tag='four_per')
        # ローソク足
        self.canvas.create_line(10+self.candle_width//2, defy, 10 +
                                self.candle_width//2, defy, tag='line'+str(self.minutes_num))
        self.canvas.create_rectangle(10, defy, 10+self.candle_width,
                                     defy, fill='red', tag='rect'+str(self.minutes_num))
        # 価格表示
        self.canvas.create_text(60, defy, text='', tag='value')

        for index, data in row_df.iterrows():
            if self.stop_event.is_set():
                print('stop')
                break
            time.sleep(0.01)
            contract_price = int(data['約定値'])
            # ローソク足の処理
            gap = contract_price-ini_val
            candle_sx = 10 + (3+self.candle_width)*self.minutes_num
            candle_sy = recsy
            candle_fx = candle_sx+self.candle_width
            candle_fy = defy-gap*self.candle_rate
            linex = candle_sx+self.candle_width//2
            # 2%と4%の線の処理
            two_per_y = defy-(contract_price*1.02-ini_val) * self.candle_rate
            four_per = contract_price*1.04
            four_per_y = defy-(contract_price*1.04-ini_val)*self.candle_rate
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
                print(str(self.minutes_num)+' '+split5m.strftime('%H:%M:%S'))
                self.minutes_num += 1
                if self.minutes_num >= 102:
                    self.minutes_num -= 1
                    # 102本以上の足を表示しようとした場合には最初の足を削除してほかの足をずらす
                    self.canvas.delete('line0')
                    self.canvas.delete('rect0')
                    self.canvas.delete('sell_volume0')
                    self.canvas.delete('buy_volume0')
                    for i in range(self.minutes_num):
                        # 名前変更
                        self.canvas.itemconfig(
                            'line'+str(i+1), tag='line'+str(i))
                        self.canvas.dtag('line'+str(i), 'line'+str(i+1))
                        self.canvas.itemconfig(
                            'rect'+str(i+1), tag='rect'+str(i))
                        self.canvas.dtag('rect'+str(i), 'rect'+str(i+1))
                        self.canvas.itemconfig(
                            'sell_volume'+str(i+1), tag='sell_volume'+str(i))
                        self.canvas.dtag('sell_volume'+str(i),
                                         'sell_volume'+str(i+1))
                        self.canvas.itemconfig(
                            'buy_volume'+str(i+1), tag='buy_volume'+str(i))
                        self.canvas.dtag('buy_volume'+str(i),
                                         'buy_volume'+str(i+1))
                        # 位置変更
                        self.canvas.move('line'+str(i),
                                         -(3+self.candle_width), 0)
                        self.canvas.move('rect'+str(i),
                                         -(3+self.candle_width), 0)
                        self.canvas.move('sell_volume'+str(i),
                                         -(3+self.candle_width), 0)
                        self.canvas.move('buy_volume'+str(i),
                                         -(3+self.candle_width), 0)
                recsy = defy-gap*self.candle_rate
                # ローソク足の処理
                candle_sx = 10 + (3+self.candle_width)*self.minutes_num
                candle_sy = recsy
                candle_fx = candle_sx+self.candle_width
                candle_fy = defy-gap*self.candle_rate
                # ひげの処理
                max = gap
                min = gap
                line_sy = defy-max*self.candle_rate
                line_fy = defy-min*self.candle_rate
                linex = candle_sx+self.candle_width//2
                # 出来高表示処理
                if buy_dir:
                    buy_volume = int(data['出来高'])
                    sell_volume = 0
                else:
                    buy_volume = 0
                    sell_volume = int(data['出来高'])
                sell_sy = 450
                sell_fy = sell_sy-sell_volume*self.volume_rate
                buy_sy = sell_fy
                buy_fy = buy_sy-buy_volume*self.volume_rate
                self.canvas.create_line(linex, buy_sy, linex, buy_fy, width=5, fill=buy_col,
                                        tag='buy_volume'+str(self.minutes_num))
                self.canvas.create_line(linex, sell_sy, linex, sell_fy, width=5, fill=sell_col,
                                        tag='sell_volume'+str(self.minutes_num))
                # ローソク足
                self.canvas.create_line(linex, line_sy, linex,
                                        line_fy, tag='line'+str(self.minutes_num))
                self.canvas.create_rectangle(
                    candle_sx, candle_sy, candle_fx, candle_fy, fill='red', tag='rect'+str(self.minutes_num))
            else:
                # 足
                self.canvas.coords('rect'+str(self.minutes_num),
                                   candle_sx, candle_sy, candle_fx, candle_fy)
                if recsy < candle_fy:
                    self.canvas.itemconfig(
                        'rect'+str(self.minutes_num), fill='blue')
                else:
                    self.canvas.itemconfig(
                        'rect'+str(self.minutes_num), fill='red')
                # ヒゲ
                if gap > max:
                    max = gap
                if gap < min:
                    min = gap
                line_sy = defy-max*self.candle_rate
                line_fy = defy-min*self.candle_rate
                self.canvas.coords('line'+str(self.minutes_num), linex,
                                   line_sy, linex, line_fy)
                # 出来高
                sell_sy = 450
                sell_fy = sell_sy-sell_volume*self.volume_rate
                buy_sy = sell_fy
                buy_fy = buy_sy-buy_volume*self.volume_rate
                self.canvas.coords('buy_volume'+str(self.minutes_num),
                                   linex, buy_sy, linex, buy_fy)
                self.canvas.coords('sell_volume'+str(self.minutes_num),
                                   linex, sell_sy, linex, sell_fy)
                # 出来高が長すぎる時の処理
                if sell_sy-buy_fy > 150:
                    self.volume_rate = int(self.volume_rate/1.1)
                    for i in range(self.minutes_num):
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
                # ローソク足が範囲外の時の処理
                if self.min_val > contract_price or four_per+10 > self.max_val:
                    pre_min_val = self.min_val
                    if self.min_val > contract_price:
                        self.min_val = contract_price
                    elif self.max_val < four_per+10:
                        self.max_val = four_per+10
                    pre_candle_rate = self.candle_rate
                    self.candle_rate = 300/(self.max_val-self.min_val)
                    # 今のローソク足の処理
                    defy = 300-(ini_val-self.min_val)*self.candle_rate
                    recsy = pos_correct(
                        recsy, pre_candle_rate, self.candle_rate, pre_min_val, self.min_val)
                    # 過去のローソク足の処理
                    recal_past_chart(self.canvas, self.minutes_num, pre_candle_rate,
                         self.candle_rate, pre_min_val, self.min_val)

            # 価格の表示
            self.canvas.itemconfig('value', text=data['約定値'])
            self.canvas.coords('value', candle_fx+40, candle_fy)

# recal_past_chatでつかう関数
def pos_correct(pre_pos, pre_candle_rate, candle_rate, pre_min_val, min_val):
    return 300-(((300-pre_pos)/pre_candle_rate+pre_min_val)-min_val)*candle_rate

# チャートの倍率が変更された際に過去チャートの倍率を変更する処理
# canvas:tkinter.canvas
# minutes_num:チャートの足数
# pre_candle_rate:前の倍率
# candle_rate:変更後の倍率
# pre_min_val:前の最小値の値
# min_val:今の最小値の値（pre_min_valと変わらない可能性もある）
def recal_past_chart(canvas, minutes_num, pre_candle_rate, candle_rate, pre_min_val, min_val):
    for i in range(minutes_num):
        # 前の価格差をだして再計算する
        for item in ['rect', 'line']:
            sx, sy, fx, fy = canvas.coords(item+str(i))
            sy = pos_correct(sy, pre_candle_rate, candle_rate, pre_min_val, min_val)
            fy = pos_correct(fy, pre_candle_rate, candle_rate, pre_min_val, min_val)
            canvas.coords(item+str(i), sx,sy, fx, fy)


def main():
    print()


if __name__ == '__main__':
    main()
