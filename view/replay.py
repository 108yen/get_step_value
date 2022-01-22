import tkinter
import time
import threading
import pandas as pd
from datetime import datetime, timedelta
from plot_chart import UpdateCanvas
import plot_past_chart

# todo：高値とか低値が狭まった時に倍率戻す処理
# todo：歩値を出す（500万以上は強調）
# todo：５分足のデータも別途保存したい


def stop_button_click(event):
    global uc
    uc.stop()


def start_button_click(event):
    global uc
    uc.start()


def suspend_button_click(event):
    global uc
    uc.suspend()

def canvas_layout(canvas):

    # 出来高とチャートの分離線
    canvas.create_line(0, 450-150, 800, 450-150, tag='split0')
    canvas.create_line(730, 0, 730, 450, tag='split1')
    canvas.create_line(800, 0, 800, 450, tag='split2')
    canvas.create_text(830, 15, text='時刻', tag='label_time', font=('', 10))
    canvas.create_text(880, 15, text='現在値', tag='label_value', font=('', 10))
    canvas.create_text(930, 15, text='出来高', tag='label_volume', font=('', 10))
    # canvas.create_line(853, 0, 853, 450, fill='#c0c0c0', tag='split3')
    # canvas.create_line(903, 0, 903, 450, fill='#c0c0c0', tag='split4')
    canvas.create_line(953, 0, 953, 450, fill='#c0c0c0', tag='split5')
    canvas.create_rectangle(953, 2, 968, 450, tag='progress_bar_outline',
                            outline='#c0c0c0')
    canvas.create_rectangle(953, 450, 968, 450, tag='progress_bar',
                            outline='#c0c0c0', fill='#c0c0c0')
    canvas.create_line(800, 30, 953, 30, tag='step_vsplit0')
    for i in range(1, (450-30)//20):  # 21個
        y = 30+20*i
        canvas.create_line(800, y, 953, y, fill='#c0c0c0',
                           tag='step_vsplit'+str(i))
    for i in range((450-30)//20):
        y = 40+20*i
        canvas.create_rectangle(
            801, y-9, 952, y+9, tag='step_volume_rec'+str(i), outline='white')
        canvas.create_text(
            828, y, text='', tag='step_time'+str(i), font=('', 10))
        canvas.create_text(880, y, text='',
                           tag='step_value'+str(i), font=('', 10))
        canvas.create_text(930, y, text='',
                           tag='step_volume'+str(i), font=('', 10))

def main():
    CODE = '7370'
    DATE = '20220121'
    PREDATE = '20220120'
    CANDLE_WIDTH = 4

    root = tkinter.Tk()
    root.configure(bg='white')
    root.geometry("1000x500")  # ウインドウサイズ（「幅x高さ」で指定）
    # 銘柄リスト：https://www.jpx.co.jp/markets/statistics-equities/misc/01.html
    codename_list = pd.read_csv(
        'data/code_list.csv', header=0, encoding='utf8')
    try:
        title=codename_list[codename_list['コード'] == 7370]['銘柄名'].values[0]
    except IndexError:
        title='銘柄リストにない銘柄コード'
    root.title(title)


    # キャンバスエリア
    canvas = tkinter.Canvas(root, width=980, height=450, bg='white')
    canvas_layout(canvas)
    candle_rate, volume_rate, max_val, min_val, index = \
        plot_past_chart.plot(canvas, CODE, PREDATE)
    # キャンバスを動かすやつ
    global uc
    uc = UpdateCanvas(canvas, CODE, DATE, CANDLE_WIDTH,
                      candle_rate, volume_rate, max_val, min_val, index)

    frame_tool_bar = tkinter.Frame(root, borderwidth=2, relief=tkinter.SUNKEN)
    start_button = tkinter.Button(
        frame_tool_bar,
        text="スタート",
        highlightbackground='black',
        fg='black',
    )
    start_button.pack(side='left')
    start_button.bind("<ButtonPress>", start_button_click)
    stop_button = tkinter.Button(
        frame_tool_bar,
        text="ストップ",
        highlightbackground='black',
        fg='black',
    )
    stop_button.pack(side='left')
    stop_button.bind("<ButtonPress>", stop_button_click)
    frame_tool_bar.pack(fill=tkinter.X)
    suspend_button = tkinter.Button(
        frame_tool_bar,
        text="一時停止",
        highlightbackground='black',
        fg='black',
    )
    suspend_button.pack(side='left')
    suspend_button.bind("<ButtonPress>", suspend_button_click)
    frame_tool_bar.pack(fill=tkinter.X)

    canvas.pack()
    root.mainloop()


if __name__ == '__main__':
    main()
