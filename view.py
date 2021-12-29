import tkinter
import time
import threading
import pandas as pd
from datetime import datetime, timedelta

# todo：倍率変更、範囲を超えた時の位置変更、出来高都下の表示、昼のデータをのぞく処理、2%の線をつける

root = tkinter.Tk()
root.title(u"TkinterのCanvasを使ってみる")
root.geometry("800x450")  # ウインドウサイズ（「幅x高さ」で指定）

# キャンバスエリア
canvas = tkinter.Canvas(root, width=800, height=450)


def split_span_by_5min(start_time, end_time):
    """
    start_time, end_time 間を5分毎に区切ったリストにして返す
    (end_timeは含まない)
    param start_time: datetime.datetime
    param end_time:   datetime.datetime
    return list = [datetime.datetime,..]
    """
    span_list = list()
    handle_time = start_time
    while(True):
        span_list.append(handle_time)
        next_time = handle_time + timedelta(minutes=5)
        if next_time < end_time:
            handle_time = next_time
        else:
            break

    return span_list


def start_button_click(event):
    th = threading.Thread(target=update_canvas, args=())
    th.start()
    # canvas.coords('rect1', 10, 10, 20, 90)


def update_canvas():
    fname = '4418_20211229_1130.csv'
    input_fname = 'data/'+fname
    row_df = pd.read_csv(input_fname, header=0, index_col=0,
                         encoding='cp932').iloc[::-1]
    ini_val = int(row_df[:1]['約定値'].values[0])
    defy = 200  # y軸の基準の位置
    recsy = 200  # その足のスタートの位置
    max = 0
    min = 0
    minutes_num = 0
    split5m = datetime.strptime("09:05:00", '%H:%M:%S')
    ini_time = datetime.strptime(row_df[:1]['時刻'].values[0], '%H:%M:%S').time()
    while ini_time > split5m.time():
        split5m = split5m+timedelta(minutes=5)

    canvas.create_line(15, defy, 15, defy, tag='line0')
    canvas.create_rectangle(10, defy, 20, defy, fill='red', tag='rect0')
    canvas.create_text(60, defy, text='', tag='value')

    for index, data in row_df.iterrows():
        time.sleep(0.01)
        gap = int(data['約定値'])-ini_val
        sx = 10 + 13*minutes_num
        sy = recsy
        fx = sx+10
        fy = defy-gap
        linex = sx+5
        # 5分足を分けるための処理
        if split5m.time() < datetime.strptime(data['時刻'], '%H:%M:%S').time():
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
            canvas.create_line(linex, defy-max, linex, defy -
                               min, tag='line'+str(minutes_num))
            canvas.create_rectangle(
                sx, sy, fx, fy, fill='red', tag='rect'+str(minutes_num))
        else:
            canvas.coords('rect'+str(minutes_num), sx, sy, fx, fy)
            if gap > max:
                max = gap
            if gap < min:
                min = gap
            canvas.coords('line'+str(minutes_num), linex,
                          defy-max, linex, defy-min)
            if recsy < fy:
                canvas.itemconfig('rect'+str(minutes_num), fill='blue')
            else:
                canvas.itemconfig('rect'+str(minutes_num), fill='red')
        # 価格の表示
        canvas.itemconfig('value',text=data['約定値'])
        canvas.coords('value',fx+40,fy)
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
    )
    start_button.pack()
    start_button.bind("<ButtonPress>", start_button_click)

    canvas.place(x=0, y=0)
    root.mainloop()


if __name__ == '__main__':
    main()
