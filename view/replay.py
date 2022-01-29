import tkinter
from tkinter import ttk
import time
import threading
import pandas as pd
from datetime import datetime, timedelta,date
from plot_chart import UpdateCanvas
import plot_past_chart
import jpholiday

# todo：高値とか低値が狭まった時に倍率戻す処理
# todo：歩値を出す（500万以上は強調）
# todo：５分足のデータも別途保存したい

# 祝日を独自に追加
class Oliginal_Holiday(jpholiday.OriginalHoliday):
    def _is_holiday(self, DATE):
        if DATE == date(2022, 1, 3):
            return True
        return False

    def _is_holiday_name(self, date):
        return '特別休暇'

def stop_button_click(event):
    global uc
    uc.stop()


def start_button_click(event):
    global uc
    uc.start()


def suspend_button_click(event):
    global uc
    uc.suspend()

def buy_button_click(event):
    global uc
    uc.buy()

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
    # canvas.create_text(998, 15, text='購入時刻', tag='label_time', font=('', 8))
    # canvas.create_text(1048, 15, text='購入価格', tag='label_value', font=('', 8))
    # canvas.create_text(1098, 15, text='売却時刻', tag='label_volume', font=('', 8))
    # canvas.create_text(1148, 15, text='売却価格', tag='label_value', font=('', 8))
    # canvas.create_text(1198, 15, text='利益', tag='label_volume', font=('', 8))
    # canvas.create_line(968, 30, 1220, 30, tag='vsplit0')
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

# date=datetime.date
def is_bisday(in_date):
    # Date = datetime.date(int(DATE[0:4]), int(DATE[4:6]), int(DATE[6:8]))
    if in_date.weekday() >= 5 or jpholiday.is_holiday(in_date):
        return False
    else:
        return True

# in:date=string "yyyymmdd"
# out:string "yyyymmdd"


def pre_bisday(in_date):
    tmp_date = date(int(in_date[0:4]), int(in_date[4:6]),
                             int(in_date[6:8]))-timedelta(days=1)
    while not is_bisday(tmp_date):
        tmp_date = tmp_date-timedelta(days=1)
    return tmp_date.strftime('%Y%m%d')

def main():
    CODE = '9211'
    DATE = '20220127'
    PREDATE = pre_bisday(DATE)  # 1/3が休日
    CANDLE_WIDTH = 4

    root = tkinter.Tk()
    root.configure(bg='white')
    root.geometry("1000x700")  # ウインドウサイズ（「幅x高さ」で指定）
    # 銘柄リスト：https://www.jpx.co.jp/markets/statistics-equities/misc/01.html
    codename_list = pd.read_csv(
        'data/code_list.csv', header=0, encoding='utf8')
    try:
        title=codename_list[codename_list['コード'] == int(CODE)]['銘柄名'].values[0]
    except IndexError:
        title='銘柄リストにない銘柄コード'
    root.title(title)



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
    buy_button = tkinter.Button(
        frame_tool_bar,
        text="購入",
        highlightbackground='black',
        fg='black',
    )
    buy_button.pack(side='left')
    buy_button.bind("<ButtonPress>", buy_button_click)
    frame_tool_bar.pack(fill=tkinter.X)

    side_panel = tkinter.Frame(root, relief=tkinter.SUNKEN)
    # キャンバスエリア
    canvas = tkinter.Canvas(side_panel, width=1000, height=450, bg='white')
    canvas_layout(canvas)
    candle_rate, volume_rate, max_val, min_val, index = \
        plot_past_chart.plot(canvas, CODE, PREDATE)
    canvas.pack()

    tree_column = ('buy_time', 'buy_value',
                   'sell_time', 'sell_value', 'profit','prof_rate')
    tree = ttk.Treeview(side_panel)
    tree['columns']=tree_column
    tree["show"] = "headings"
    tree.column('buy_time', width=70)
    tree.column('buy_value', width=70)
    tree.column('sell_time', width=70)
    tree.column('sell_value', width=70)
    tree.column('profit', width=70)
    tree.column('prof_rate', width=70)
    tree.heading('buy_time', text='購入時刻')
    tree.heading('buy_value', text='購入価格')
    tree.heading('sell_time', text='売却時刻')
    tree.heading('sell_value', text='売却価格')
    tree.heading('profit', text='利益')
    tree.heading('prof_rate',text='利益率')
    tree.pack(side=tkinter.LEFT)

    side_panel.pack(side=tkinter.LEFT, fill=tkinter.Y)

    # キャンバスを動かすやつ
    global uc
    uc = UpdateCanvas(tree,canvas, CODE, DATE, CANDLE_WIDTH,
                      candle_rate, volume_rate, max_val, min_val, index)

    root.mainloop()


if __name__ == '__main__':
    main()
    # print(pre_bisday('20220104'))


