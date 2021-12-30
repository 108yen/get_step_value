import tkinter
import time
import threading
import pandas as pd
from datetime import datetime, timedelta

# todo：倍率変更、範囲を超えた時の位置変更、昼のデータをのぞく処理、2%の線をつける、スレッドをクラスで書き出す

root = tkinter.Tk()
root.title(u"GEI")
root.geometry("800x450")  # ウインドウサイズ（「幅x高さ」で指定）

# キャンバスエリア
canvas = tkinter.Canvas(root, width=800, height=450)


def stop_button_click(event):
    stop = True


def start_button_click(event):
    th = threading.Thread(target=update_canvas, args=())
    th.start()
    # canvas.coords('rect1', 10, 10, 20, 90)


def update_canvas():
    fname = '9212_20211230_1500.csv'
    input_fname = 'data/'+fname
    row_df = pd.read_csv(input_fname, header=0, index_col=0,
                         encoding='cp932').iloc[::-1]
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

    canvas.create_line(15, 450, 15, 450, width=5,
                       fill=buy_col, tag='buy_volume0')
    canvas.create_line(15, 450, 15, 450, width=5,
                       fill=sell_col, tag='sell_volume0')
    canvas.create_line(0,450-150,800,450-150)

    canvas.create_line(15, defy, 15, defy, tag='line0')
    canvas.create_rectangle(10, defy, 20, defy, fill='red', tag='rect0')
    canvas.create_text(60, defy, text='', tag='value')

    for index, data in row_df.iterrows():
        time.sleep(0.01)
        contract_price = int(data['約定値'])
        gap = contract_price-ini_val
        sx = 10 + 13*minutes_num
        sy = recsy
        fx = sx+10
        fy = defy-gap
        linex = sx+5
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
            split5m = split5m+timedelta(minutes=5)
            minutes_num += 1
            recsy = defy-gap
            max = gap
            min = gap
            sx = 10 + 13*minutes_num
            sy = recsy
            fx = sx+10
            fy = defy-gap
            linex = sx+5
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
            canvas.create_line(linex, buy_sy, linex, buy_fy, width=5, fill=buy_col,
                               tag='buy_volume'+str(minutes_num))
            canvas.create_line(linex, sell_sy, linex, sell_fy, width=5, fill=sell_col,
                               tag='sell_volume'+str(minutes_num))
            canvas.create_line(linex, defy-max, linex,
                               defy - min, tag='line'+str(minutes_num))
            canvas.create_rectangle(
                sx, sy, fx, fy, fill='red', tag='rect'+str(minutes_num))
        else:
            # 足
            canvas.coords('rect'+str(minutes_num), sx, sy, fx, fy)
            if recsy < fy:
                canvas.itemconfig('rect'+str(minutes_num), fill='blue')
            else:
                canvas.itemconfig('rect'+str(minutes_num), fill='red')
            # ヒゲ
            if gap > max:
                max = gap
            if gap < min:
                min = gap
            canvas.coords('line'+str(minutes_num), linex,
                          defy-max, linex, defy-min)
            # 出来高
            sell_sy = 450
            sell_fy = sell_sy-sell_volume//vol_mag
            buy_sy = sell_fy
            buy_fy = buy_sy-buy_volume//vol_mag
            canvas.coords('buy_volume'+str(minutes_num),
                          linex, buy_sy, linex, buy_fy)
            canvas.coords('sell_volume'+str(minutes_num),
                          linex, sell_sy, linex, sell_fy)
            # 出来高が長すぎる時の処理
            if sell_sy-buy_fy > 150:
                vol_mag=int(vol_mag*1.1)
                for i in range(minutes_num):
                    sell_sx, sell_sy, sell_fx, sell_fy = canvas.coords(
                        'sell_volume'+str(i))
                    buy_sx, buy_sy, buy_fx, buy_fy = canvas.coords(
                        'buy_volume'+str(i))
                    sell_ln = ((sell_sy-sell_fy)*10)//11
                    buy_ln = ((buy_sy-buy_fy)*10)//11
                    sell_fy = sell_sy-sell_ln
                    buy_sy = sell_fy
                    buy_fy = buy_sy-buy_ln
                    canvas.coords('sell_volume'+str(i), sell_sx,
                                  sell_sy, sell_fx, sell_fy)
                    canvas.coords('buy_volume'+str(i), buy_sx,
                                  buy_sy, buy_fx, buy_fy)
        # 価格の表示
        canvas.itemconfig('value', text=data['約定値'])
        canvas.coords('value', fx+40, fy)
        # チャートが上に激突しないようにする処理
        if fy < 20:
            defy += 10
            recsy += 10
            for i in range(minutes_num):
                canvas.move('line'+str(i), 0, 10)
                canvas.move('rect'+str(i), 0, 10)
        print(data['時刻'])
        # print(gap)


def main():

    start_button = tkinter.Button(
        root,
        text="スタート",
        fg='black',
    )
    start_button.pack()
    start_button.bind("<ButtonPress>", start_button_click)
    stop_button = tkinter.Button(
        root,
        text="ストップ",
        fg='black',
    )
    stop_button.pack()
    stop_button.bind("<ButtonPress>", stop_button_click)

    canvas.place(x=0, y=0)
    root.mainloop()


if __name__ == '__main__':
    main()
