import tkinter
import time
import threading
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import math
import tickchart

# from xarray import concat

"""
ファイルを読み込んでcanvasにチャートを描画
canvas: tkinter.Canvas
code:   string
date:   string
candle_width    int
"""


class UpdateCanvas(threading.Thread):
    def __init__(self, tree, canvas, code, date, candle_width, candle_rate, volume_rate, max_val, min_val, minutes_num):
        super(UpdateCanvas, self).__init__()
        self.tree = tree
        self.canvas = canvas
        self.code = code
        self.date = date
        self.candle_width = candle_width
        self.candle_rate = candle_rate
        self.volume_rate = volume_rate
        self.max_val = max_val
        self.min_val = min_val
        self.minutes_num = minutes_num+1 if minutes_num!=0 else 0 # 次の足から描画するので
        self.stop_event = threading.Event()
        self.suspend_event = False
        self.buy_event = False
        self.setDaemon(True)
        self.tchart=tickchart.Tick_Chart(canvas,0,452)

    def stop(self):
        self.stop_event.set()

    def suspend(self):
        self.suspend_event = not self.suspend_event

    def buy(self):
        self.buy_event = True

    def run(self):
        # 午前午後分かれてないパターン
        fname = 'data/'+self.date+'/'+self.code+'.csv'
        row_df = pd.read_csv(fname, header=0, index_col=0,
                             encoding='cp932').iloc[::-1].reset_index(drop=True)
        # 始まりの値が前日の高値と低値の外だったら倍率も変える必要がある
        ini_val = int(row_df[:1]['約定値'].values[0])
        defy = 0
        # 範囲外だった場合倍率も変更する必要がある
        if (self.min_val > ini_val or ini_val > self.max_val) and self.minutes_num!=0:
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
        # vwap表示のための変数
        sum_volume = 0
        trading_price = 0
        vwap_sx, vwap_sy, vwap_fx, vwap_fy = self.canvas.coords(
            'vwap'+str(self.minutes_num-1)) if self.minutes_num != 0 else (0, 200, 0, 200)
        vwap_sx = vwap_fx
        vwap_sy = vwap_fy
        vwap_fx = 10+(3+self.candle_width) * \
            self.minutes_num+self.candle_width//2
        vwap_fy = defy
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
        # vwap(前日の終わりとつなげる)
        self.canvas.create_line(vwap_sx, vwap_sy, vwap_fx, vwap_fy,
                                fill='#ff6347', tag='vwap'+str(self.minutes_num))
        # ローソク足
        self.canvas.create_line(10+self.candle_width//2, defy, 10 +
                                self.candle_width//2, defy, tag='line'+str(self.minutes_num))
        self.canvas.create_rectangle(10, defy, 10+self.candle_width,
                                     defy, fill='red', tag='rect'+str(self.minutes_num))
        # vwap乖離率表示
        self.canvas.create_text(
            35, 15, text='', tag='vwap_dev_rate', font=('', 25))

        # 購入処理用の変数
        buy_time = ''
        buy_val = -1
        sell_val = -1
        losscut_val = -1
        profit = -1
        prof_rate = -1
        p_volume = -1
        tree_iid = -1

        # リプレイ処理
        for index, data in row_df.iterrows():
            # 停止一時停止の処理
            if self.stop_event.is_set():
                self.tchart.delete()
                print('stop')
                break
            if self.suspend_event:
                while self.suspend_event:
                    time.sleep(0.1)
            time.sleep(0.01)
            self.tchart.update_volumechart(data['約定値'],data['出来高'])
            contract_price = int(data['約定値'])
            # 購入した際の処理
            if self.buy_event:
                self.buy_event = False
                if buy_val == -1:
                    buy_time = data['時刻']
                    buy_val = contract_price
                    p_volume = math.floor(10000/buy_val)*100
                    sell_val = math.ceil(buy_val*1.02)
                    losscut_val = math.ceil(buy_val*0.97)
                    profit = (contract_price-buy_val)*p_volume
                    tree_iid = self.tree.insert(parent='', index='end', values=(
                        buy_time, buy_val, '', '('+str(sell_val)+')', "{:,}".format(profit), 0))
            # 利確
            elif (sell_val < contract_price or losscut_val > contract_price) and buy_val != -1:
                self.tree.item(tree_iid, values=(
                    buy_time, buy_val, data['時刻'], contract_price, "{:,}".format(profit), prof_rate))
                buy_time = ''
                buy_val = -1
                sell_val = -1
                losscut_val = -1
                profit = -1
                prof_rate = -1
                p_volume = -1
                tree_iid = -1
            elif buy_val != -1:
                profit = (contract_price-buy_val)*p_volume
                prof_rate = round(((contract_price-buy_val)/buy_val)*100, 2)
                self.tree.item(tree_iid, values=(
                    buy_time, buy_val, '', '('+str(sell_val)+')',  "{:,}".format(profit), prof_rate))

            # プログレスバーの処理 長さが448
            prog_bar_y = 450-448*(index/len(row_df))
            self.canvas.coords('progress_bar', 953, 450, 968, prog_bar_y)
            # 歩みね表示の処理
            step_view = row_df[index-20 if index >= 20 else 0:index+1]\
                .reset_index(drop=True)
            # 色付け処理
            pre_buy_flag = True
            step_view_l = len(step_view)
            # 500万以上の買いの強調初期化
            detect_amount_1 = 5000000
            detect_amount_2 = 2000000
            emphasis_col_1 = 'red'
            emphasis_col_2 = 'orange'
            for i in range(21):
                self.canvas.itemconfig(
                    'step_volume_rec'+str(i), outline='white')
            # 最初の値
            if index < 21:
                pre_buy_flag = True
                self.canvas.itemconfig(
                    'step_volume'+str(index), fill='red')
            else:
                first_buy_flag_i = 0
                while index-21-first_buy_flag_i >= 0:
                    if row_df[index-21-first_buy_flag_i:index-20-first_buy_flag_i]['約定値'].values[0] < \
                            row_df[index-20-first_buy_flag_i:index-19-first_buy_flag_i]['約定値'].values[0]:
                        pre_buy_flag = True
                        self.canvas.itemconfig(
                            'step_volume'+str(step_view_l-1), fill='red')
                        if step_view[0:1]['約定値'].values[0]*step_view[0:1]['出来高'].values[0] > detect_amount_1:
                            self.canvas.itemconfig('step_volume_rec'+str(step_view_l-1),
                                                   outline=emphasis_col_1)
                        elif step_view[0:1]['約定値'].values[0]*step_view[0:1]['出来高'].values[0] > detect_amount_2:
                            self.canvas.itemconfig('step_volume_rec'+str(step_view_l-1),
                                                   outline=emphasis_col_2)
                        break
                    elif row_df[index-21-first_buy_flag_i:index-20-first_buy_flag_i]['約定値'].values[0] > \
                            row_df[index-20-first_buy_flag_i:index-19-first_buy_flag_i]['約定値'].values[0]:
                        pre_buy_flag = False
                        self.canvas.itemconfig(
                            'step_volume'+str(step_view_l-1), fill='blue')
                        break
                    first_buy_flag_i += 1
            # 最初の売買以降の処理
            for sv_index in range(1, step_view_l):
                if step_view[sv_index-1:sv_index]['約定値'].values[0] < step_view[sv_index:sv_index+1]['約定値'].values[0]:
                    pre_buy_flag = True
                    self.canvas.itemconfig(
                        'step_volume'+str(step_view_l-sv_index-1), fill='red')
                    if step_view[sv_index:sv_index+1]['約定値'].values[0] *\
                            step_view[sv_index:sv_index+1]['出来高'].values[0] > detect_amount_1:
                        self.canvas.itemconfig('step_volume_rec'+str(step_view_l-sv_index-1),
                                               outline=emphasis_col_1)
                    elif step_view[sv_index:sv_index+1]['約定値'].values[0] *\
                            step_view[sv_index:sv_index+1]['出来高'].values[0] > detect_amount_2:
                        self.canvas.itemconfig('step_volume_rec'+str(step_view_l-sv_index-1),
                                               outline=emphasis_col_2)
                elif step_view[sv_index-1:sv_index]['約定値'].values[0] > step_view[sv_index:sv_index+1]['約定値'].values[0]:
                    pre_buy_flag = False
                    self.canvas.itemconfig(
                        'step_volume'+str(step_view_l-sv_index-1), fill='blue')
                else:
                    if pre_buy_flag:
                        self.canvas.itemconfig(
                            'step_volume'+str(step_view_l-sv_index-1), fill='red')
                        if step_view[sv_index:sv_index+1]['約定値'].values[0] *\
                                step_view[sv_index:sv_index+1]['出来高'].values[0] > detect_amount_1:
                            self.canvas.itemconfig('step_volume_rec'+str(step_view_l-sv_index-1),
                                                   outline=emphasis_col_1)
                        elif step_view[sv_index:sv_index+1]['約定値'].values[0] *\
                                step_view[sv_index:sv_index+1]['出来高'].values[0] > detect_amount_2:
                            self.canvas.itemconfig('step_volume_rec'+str(step_view_l-sv_index-1),
                                                   outline=emphasis_col_2)
                    else:
                        self.canvas.itemconfig(
                            'step_volume'+str(step_view_l-sv_index-1), fill='blue')

            step_view = step_view.iloc[::-1].reset_index(drop=True)
            for sv_index, sv_data in step_view.iterrows():
                self.canvas.itemconfig(
                    'step_time'+str(sv_index), text=sv_data['時刻'])
                self.canvas.itemconfig(
                    'step_value'+str(sv_index), text=int(sv_data['約定値']))
                self.canvas.itemconfig(
                    'step_volume'+str(sv_index), text=int(sv_data['出来高']))
            # ローソク足の処理
            gap = contract_price-ini_val
            candle_sx = 10 + (3+self.candle_width)*self.minutes_num
            candle_sy = recsy
            candle_fx = candle_sx+self.candle_width
            candle_fy = defy-gap*self.candle_rate
            linex = candle_sx+self.candle_width//2
            # 2%と4%の線の処理
            if buy_val == -1:
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
            # VWAP用の処理
            sum_volume += int(data['出来高'])
            trading_price += int(data['出来高'])*contract_price
            vwap_fy = defy-(trading_price/sum_volume-ini_val)*self.candle_rate
            # 5分足を分けるための処理
            if split5m.time() <= datetime.strptime(data['時刻'], '%H:%M:%S').time():
                while datetime.strptime(data['時刻'], '%H:%M:%S').time() >= split5m.time():
                    split5m = split5m+timedelta(minutes=5)
                # print(split5m.strftime('%H:%M:%S'))
                self.minutes_num += 1
                if self.minutes_num >= 102:
                    self.minutes_num -= 1
                    # 102本以上の足を表示しようとした場合には最初の足を削除してほかの足をずらす
                    self.canvas.delete('line0')
                    self.canvas.delete('rect0')
                    self.canvas.delete('sell_volume0')
                    self.canvas.delete('buy_volume0')
                    self.canvas.delete('vwap0')
                    for i in range(self.minutes_num):
                        for item in ['line', 'rect', 'sell_volume', 'buy_volume', 'vwap']:
                            # 名前変更
                            self.canvas.itemconfig(
                                item+str(i+1), tag=item+str(i))
                            self.canvas.dtag(item+str(i), item+str(i+1))
                            # 位置変更
                            self.canvas.move(item+str(i),
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
                # vwapの処理
                vwap_sx = 10 + (3+self.candle_width) * \
                    (self.minutes_num-1)+self.candle_width//2
                vwap_sy = vwap_fy
                vwap_fx = linex
                vwap_fy = defy-(trading_price/sum_volume -
                                ini_val)*self.candle_rate
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
                # vwap
                self.canvas.create_line(
                    vwap_sx, vwap_sy, vwap_fx, vwap_fy, fill='#ff6347', tag='vwap'+str(self.minutes_num))
                self.canvas.lower('vwap'+str(self.minutes_num))
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
                # vwap
                self.canvas.coords('vwap'+str(self.minutes_num),
                                   vwap_sx, vwap_sy, vwap_fx, vwap_fy)
                # 出来高
                sell_sy = 450
                sell_fy = sell_sy-sell_volume*self.volume_rate
                buy_sy = sell_fy
                buy_fy = buy_sy-buy_volume*self.volume_rate
                # 出来高が長すぎる時の処理
                if sell_sy-buy_fy > 150:
                    self.volume_rate = self.volume_rate/1.1
                    for i in range(self.minutes_num):
                        sell_sx, p_sell_sy, sell_fx, p_sell_fy = self.canvas.coords(
                            'sell_volume'+str(i))
                        buy_sx, p_buy_sy, buy_fx, p_buy_fy = self.canvas.coords(
                            'buy_volume'+str(i))
                        sell_ln = ((p_sell_sy-p_sell_fy)*10)/11
                        buy_ln = ((p_buy_sy-p_buy_fy)*10)/11
                        p_sell_fy = p_sell_sy-sell_ln
                        p_buy_sy = p_sell_fy
                        p_buy_fy = p_buy_sy-buy_ln
                        self.canvas.coords('sell_volume'+str(i), sell_sx,
                                           p_sell_sy, sell_fx, p_sell_fy)
                        self.canvas.coords('buy_volume'+str(i), buy_sx,
                                           p_buy_sy, buy_fx, p_buy_fy)
                else:
                    self.canvas.coords('buy_volume'+str(self.minutes_num),
                                       linex, buy_sy, linex, buy_fy)
                    self.canvas.coords('sell_volume'+str(self.minutes_num),
                                       linex, sell_sy, linex, sell_fy)

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
                    # 今のVwapのスタート位置の処理
                    vwap_sy = pos_correct(
                        vwap_sy, pre_candle_rate, self.candle_rate, pre_min_val, self.min_val)
                    # 過去のローソク足の処理
                    recal_past_chart(self.canvas, self.minutes_num, pre_candle_rate,
                                     self.candle_rate, pre_min_val, self.min_val)

            # 価格の表示
            self.canvas.itemconfig('value', text=data['約定値'])
            self.canvas.coords('value', candle_fx+40, candle_fy)
            # vwap乖離率の表示
            vwap_dev_rate = round(
                ((contract_price-trading_price/sum_volume)/contract_price)*100, 2)
            vwap_dev_rate_col = '#808080'
            if vwap_dev_rate < -4:
                vwap_dev_rate_col = '#ff0000'
            self.canvas.itemconfig('vwap_dev_rate', text=str(
                vwap_dev_rate), fill=vwap_dev_rate_col)

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
        for item in ['rect', 'line', 'vwap']:
            sx, sy, fx, fy = canvas.coords(item+str(i))
            sy = pos_correct(sy, pre_candle_rate, candle_rate,
                             pre_min_val, min_val)
            fy = pos_correct(fy, pre_candle_rate, candle_rate,
                             pre_min_val, min_val)
            canvas.coords(item+str(i), sx, sy, fx, fy)


def main():
    print()


if __name__ == '__main__':
    main()
