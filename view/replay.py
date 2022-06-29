from multiprocessing import Process
import tkinter
from tkinter import ttk
import time
import threading
from matplotlib.pyplot import draw
import pandas as pd
from datetime import datetime, timedelta, date
from plot_chart import UpdateCanvas
import plot_past_chart
import jpholiday
import os
import locale
from sqlalchemy import create_engine
import mysql.connector
import db_conf

# todo：高値とか低値が狭まった時に倍率戻す処理
# todo：５分足のデータも別途保存したい
# todo:日足表示したい
# todo:ティックチャート

# 祝日を独自に追加


class Oliginal_Holiday(jpholiday.OriginalHoliday):
    def _is_holiday(self, DATE):
        if DATE == date(2022, 1, 3):
            return True
        return False

    def _is_holiday_name(self, date):
        return '特別休暇'


class Replay_Chart():
    def stop_button_click(self, event):
        self.uc.stop()

    def start_button_click(self, event):
        if not self.uc.is_alive():
            self.uc.start()

    def suspend_button_click(self, event):
        self.uc.suspend()

    def buy_button_click(self, event):
        self.uc.buy()

    def draw_chart_click(self, event):
        if self.uc.is_alive():
            self.uc.stop()
        # 消す処理
        for i in self.tree.get_children():
            self.tree.delete(i)
        for i in range((450-30)//20):
            self.canvas.itemconfig(
                'step_time'+str(i), text='')
            self.canvas.itemconfig(
                'step_value'+str(i), text='')
            self.canvas.itemconfig(
                'step_volume'+str(i), text='')
        for i in range(102):
            for item in ['line', 'rect', 'sell_volume', 'buy_volume', 'vwap']:
                self.canvas.delete(item+str(i))
        in_str = self.codelist_cb.get()[:4]
        if self.random_bln.get():
            r_pick=self.tick_filter(5000)
            code_str=str(r_pick['code'].iloc[0])
            date=r_pick['date'].dt.strftime('%Y%m%d').iloc[0]
            self.set_window_title(code_str, date)
            self.draw_p(self.tree, self.canvas,
                        code_str, date, self.CANDLE_WIDTH, self.pre_bisday(date))
        elif len(in_str) == 4 and in_str.isdecimal():
            # date=self.year_cb.get()+self.month_cb.get()+self.day_cb.get()
            date = datetime(int(self.year_cb.get()), int(
                self.month_cb.get()), int(self.day_cb.get())).strftime('%Y%m%d')
            self.set_window_title(in_str, date)
            self.draw_p(self.tree, self.canvas,
                        in_str, date, self.CANDLE_WIDTH, self.pre_bisday(date))
        else:
            print('入力コードの書式エラー')
        # print(self.code_box.get())
    def tick_filter(self,tick:int):
        engine = create_engine(
            'mysql+mysqlconnector://'+db_conf.db_user+':'+db_conf.db_pass+'@'+db_conf.db_ip+'/stock')
        code_list=pd.read_sql_query('SELECT * FROM getdate WHERE tick > '+str(tick),con=engine, parse_dates={'date':'%Y-%m-%d'})

        return code_list.sample()

    def canvas_layout(self, canvas):

        # 出来高とチャートの分離線
        canvas.create_line(0, 450-150, 800, 450-150, tag='split0')
        canvas.create_line(730, 0, 730, 450, tag='split1')
        canvas.create_line(800, 0, 800, 450, tag='split2')
        canvas.create_text(830, 15, text='時刻', tag='label_time', font=('', 10))
        canvas.create_text(880, 15, text='現在値',
                           tag='label_value', font=('', 10))
        canvas.create_text(930, 15, text='出来高',
                           tag='label_volume', font=('', 10))
        # canvas.create_line(853, 0, 853, 450, fill='#c0c0c0', tag='split3')
        # canvas.create_line(903, 0, 903, 450, fill='#c0c0c0', tag='split4')
        canvas.create_line(953, 0, 953, 450, fill='#c0c0c0', tag='split5')
        # canvas.create_line(0, 450, 1000, 450, tag='split_tickchart')
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
        # 2%と4%の線
        self.canvas.create_line(0, 0, self.canvas.winfo_width(),
                                0, width=1, fill='#3cb371', tag='two_per')
        self.canvas.create_line(0, 0, self.canvas.winfo_width(),
                                0, width=1, fill='#ffa07a', tag='four_per')
        # 価格表示
        self.canvas.create_text(60, 0, text='', tag='value')

    # date=datetime.date

    def is_bisday(self, in_date):
        # Date = datetime.date(int(DATE[0:4]), int(DATE[4:6]), int(DATE[6:8]))
        if in_date.weekday() >= 5 or jpholiday.is_holiday(in_date):
            return False
        else:
            return True

    # in:date=string "yyyymmdd"
    # out:string "yyyymmdd"

    def pre_bisday(self, in_date):
        tmp_date = date(int(in_date[0:4]), int(in_date[4:6]),
                        int(in_date[6:8]))-timedelta(days=1)
        while not self.is_bisday(tmp_date):
            tmp_date = tmp_date-timedelta(days=1)
        return tmp_date.strftime('%Y%m%d')

    def set_window_title(self, code, in_date):
        # 銘柄リスト：https://www.jpx.co.jp/markets/statistics-equities/misc/01.html
        codename_list = pd.read_csv(
            'data/code_list.csv', header=0, encoding='cp932')
        try:
            locale.setlocale(locale.LC_TIME, 'Japanese_Japan.932')
            out_date=date(int(in_date[0:4]), int(in_date[4:6]), int(in_date[6:8])).strftime('%Y-%m-%d (%a)')
            title = code+' '+codename_list[codename_list['銘柄コード']
                                           == int(code)]['銘柄名'].values[0]+'    '+out_date
        except IndexError:
            title = '銘柄リストにない銘柄コード'
        self.root.title(title)

    def __init__(self):
        CODE = '4267'
        DATE = '20220210'
        predate = self.pre_bisday(DATE)  # 1/3が休日
        self.CANDLE_WIDTH = 4

        self.root = tkinter.Tk()
        self.root.configure(bg='white')
        self.root.geometry("1000x700")  # ウインドウサイズ（「幅x高さ」で指定）
        self.root.bind("<Return>",self.buy_button_click)
        self.root.bind("<space>",self.suspend_button_click)
        # 銘柄リスト：https://www.jpx.co.jp/markets/statistics-equities/misc/01.html
        self.set_window_title(CODE, DATE)

        frame_tool_bar = tkinter.Frame(
            self.root, borderwidth=2, relief=tkinter.SUNKEN)
        start_button = tkinter.Button(
            frame_tool_bar,
            text="スタート",
            highlightbackground='black',
            fg='black',
        )
        start_button.pack(side='left')
        start_button.bind("<ButtonPress>", self.start_button_click)
        stop_button = tkinter.Button(
            frame_tool_bar,
            text="ストップ",
            highlightbackground='black',
            fg='black',
        )
        stop_button.pack(side='left')
        stop_button.bind("<ButtonPress>", self.stop_button_click)
        suspend_button = tkinter.Button(
            frame_tool_bar,
            text="一時停止",
            highlightbackground='black',
            fg='black',
        )
        suspend_button.pack(side='left')
        suspend_button.bind("<ButtonPress>", self.suspend_button_click)
        buy_button = tkinter.Button(
            frame_tool_bar,
            text="購入",
            highlightbackground='black',
            fg='black',
        )
        buy_button.pack(side='right')
        buy_button.bind("<ButtonPress>", self.buy_button_click)
        code_label = tkinter.Label(frame_tool_bar, text='銘柄コード:')
        code_label.pack(side='left')
        # self.code_box = tkinter.Entry(
        #     frame_tool_bar,
        #     width=5,
        # )
        # self.code_box.pack(side='left', padx=4)
        try:
            engine = create_engine(
                'mysql+mysqlconnector://'+db_conf.db_user+':'+db_conf.db_pass+'@'+db_conf.db_ip+'/stock')
            codename_list = pd.read_sql_query('SELECT * FROM codelist', con=engine)
            view_codelist=codename_list['code'].astype(str)+' '+codename_list['name']
        except Exception as e:
            print('dberror:'+str(e))
            codename_list = pd.read_csv(
                'data/code_list.csv', header=0, encoding='cp932',dtype=str).sort_values('銘柄コード')
            view_codelist=codename_list['銘柄コード']+' '+codename_list['銘柄名']
        self.codelist_cb = tkinter.ttk.Combobox(
            frame_tool_bar,
            width=15,
            values=tuple(view_codelist)
        )
        self.codelist_cb.pack(side='left', padx=4)
        self.year_cb = tkinter.ttk.Combobox(
            frame_tool_bar,
            width=5,
            values=('2022', '2021')
        )
        self.year_cb.current(0)
        self.year_cb.pack(side='left')
        year_label = tkinter.Label(frame_tool_bar, text='年')
        year_label.pack(side='left')
        self.month_cb = tkinter.ttk.Combobox(
            frame_tool_bar,
            width=2,
            values=tuple(range(1, 13))
        )
        self.month_cb.current(int(datetime.today().strftime('%m'))-1)
        self.month_cb.pack(side='left')
        month_label = tkinter.Label(frame_tool_bar, text='月')
        month_label.pack(side='left')
        self.day_cb = tkinter.ttk.Combobox(
            frame_tool_bar,
            width=2,
            values=tuple(range(1, 32))
        )
        self.day_cb.current(int(datetime.today().strftime('%d'))-1)
        self.day_cb.pack(side='left')
        day_label = tkinter.Label(frame_tool_bar, text='日')
        day_label.pack(side='left')
        draw_chart = tkinter.Button(
            frame_tool_bar,
            text="描画",
            highlightbackground='black',
            fg='black',
        )
        draw_chart.pack(side='left')
        draw_chart.bind("<ButtonPress>", self.draw_chart_click)
        self.random_bln=tkinter.BooleanVar()
        self.random_bln.set(True)
        random_rdo = tkinter.Checkbutton(
            frame_tool_bar,
            variable=self.random_bln,
            text="ランダム",
        )
        random_rdo.pack(side='left')
        frame_tool_bar.pack(fill=tkinter.X)

        side_panel = tkinter.Frame(self.root, relief=tkinter.SUNKEN)
        # キャンバスエリア
        self.canvas = tkinter.Canvas(
            side_panel, width=1000, height=450, bg='white')
        self.canvas_layout(self.canvas)
        self.canvas.pack()

        tree_column = ('buy_time', 'buy_value',
                       'sell_time', 'sell_value', 'profit', 'prof_rate')
        self.tree = ttk.Treeview(side_panel)
        self.tree['columns'] = tree_column
        self.tree["show"] = "headings"
        self.tree.column('buy_time', width=70)
        self.tree.column('buy_value', width=70)
        self.tree.column('sell_time', width=70)
        self.tree.column('sell_value', width=70)
        self.tree.column('profit', width=70)
        self.tree.column('prof_rate', width=70)
        self.tree.heading('buy_time', text='購入時刻')
        self.tree.heading('buy_value', text='購入価格')
        self.tree.heading('sell_time', text='売却時刻')
        self.tree.heading('sell_value', text='売却価格')
        self.tree.heading('profit', text='利益')
        self.tree.heading('prof_rate', text='利益率')
        self.tree.pack(side=tkinter.LEFT)

        side_panel.pack(side=tkinter.LEFT, fill=tkinter.Y)

        draw_thread = threading.Thread(target=self.draw_p, args=(self.tree, self.canvas,
                                                                 CODE, DATE, self.CANDLE_WIDTH, predate))
        draw_thread.start()
        self.root.mainloop()

    def draw_p(self, tree, canvas, code, DATE, CANDLE_WIDTH, predate):
        # キャンバスを動かすやつ
        if os.path.isfile('data/'+predate+'/'+code+'.csv'):
            candle_rate, volume_rate, max_val, min_val, index = \
                plot_past_chart.plot(canvas, code, predate)
        else:
            candle_rate=1
            volume_rate=1
            max_val=0
            min_val=999999
            index=0
        self.uc = UpdateCanvas(tree, canvas, code, DATE, CANDLE_WIDTH,
                               candle_rate, volume_rate, max_val, min_val, index)


if __name__ == '__main__':
    Replay_Chart()
    # print(pre_bisday('20220104'))
