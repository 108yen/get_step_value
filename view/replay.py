import tkinter
import time
import threading
import pandas as pd
from datetime import datetime, timedelta
from plot_chart import UpdateCanvas
import plot_past_chart

# todo：高値とか低値が狭まった時の処理、歩値を出す（500万以上は強調）

root = tkinter.Tk()
root.title(u"GEI")
root.configure(bg='white')
root.geometry("850x500")  # ウインドウサイズ（「幅x高さ」で指定）

CODE = '6524'
DATE = '20211230'
PREDATE = '20211229'
CANDLE_WIDTH = 4

# キャンバスエリア
canvas = tkinter.Canvas(root, width=800, height=450, bg='white')
candle_rate, volume_rate, max_val, min_val, index = \
    plot_past_chart.plot(canvas, CODE, PREDATE)
# キャンバスを動かすやつ
uc = UpdateCanvas(canvas, CODE, DATE, CANDLE_WIDTH,
                  candle_rate, volume_rate, max_val, min_val, index)


def stop_button_click(event):
    uc.stop()


def start_button_click(event):
    uc.start()


def main():
    start_button = tkinter.Button(
        root,
        text="スタート",
        highlightbackground='black',
        fg='black',
    )
    start_button.pack()
    start_button.bind("<ButtonPress>", start_button_click)
    stop_button = tkinter.Button(
        root,
        text="ストップ",
        highlightbackground='black',
        fg='black',
    )
    stop_button.pack()
    stop_button.bind("<ButtonPress>", stop_button_click)

    canvas.place(x=0, y=0)
    root.mainloop()


if __name__ == '__main__':
    main()