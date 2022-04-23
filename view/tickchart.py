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
from tqdm import tqdm

class Tick_Chart():

    def __init__(self,canvas: tkinter.Canvas,root: tkinter.Tk):
        # 倍率を管理する変数
        self.height=150
        self.heighvolume=float(1000)
        self.volumeX=(self.height/2)/self.heighvolume   #上下1000株で初期化
        self.valueX=1000
        self.canvas=canvas
        self.canvas.create_line(0, 80, 1000, 80, tag='center_line',fill='#c0c0c0')
        for i in range(200):
            self.canvas.create_rectangle(5*i,80,5*(i+1),80,tag='volumebar'+str(i))
        self.volumelist=[float(0)]*200
        self.pvalue=0
        self.buylist=[True]*200
        # self.canvas_buf=tkinter.Canvas(root, width=1000, height=160, bg='white')

    def update_chart(self,value: float,volume: float):
        self.volumelist.append(volume)
        del self.volumelist[0]
        if self.pvalue<value:
            self.buylist.append(True)
        elif self.pvalue>value:
            self.buylist.append(False)
        else:
            self.buylist.append(self.buylist[-1])
        del self.buylist[0]
        self.pvalue=value
        # 倍率処理
        maxvolume=max(self.volumelist)
        if volume>self.heighvolume:
            self.heighvolume=volume
            self.volumeX=(self.height/2)/self.heighvolume
        elif maxvolume!=self.heighvolume:
            self.heighvolume=maxvolume
            self.volumeX=(self.height/2)/self.heighvolume

        for i in range(200):
            h=self.volumelist[i]*self.volumeX
            h=h if self.buylist[i] else -h
            self.canvas.coords('volumebar'+str(i),5*i,80-h,5*(i+1),80)
            color='red' if self.buylist[i] else 'blue'
            self.canvas.itemconfig('volumebar'+str(i), fill=color)

# テスト用
def test_roop(tc:Tick_Chart,root:tkinter.Tk,canvas:tkinter.Canvas):
    row_df = pd.read_csv('data/20220422/9221.csv', header=0, index_col=0,
                            encoding='cp932').iloc[::-1].reset_index(drop=True)
    for index, data in tqdm(row_df.iterrows()):
        root.title(data['時刻'])
        tc.update_chart(data['約定値'],data['出来高'])
        canvas.update()
        # root.after(1,self.update_chart,args=(value,volume))
        # canvas.after(0,tc.update_chart(data['約定値'],data['出来高']))

if __name__ == '__main__':
    root = tkinter.Tk()
    root.configure(bg='white')
    root.geometry("1000x170")  # ウインドウサイズ（「幅x高さ」で指定）
    canvas = tkinter.Canvas(
        root, width=1000, height=160, bg='white')
    canvas.pack()

    testTC=Tick_Chart(canvas,root)
    test_th = threading.Thread(target=test_roop, args=(testTC,root,canvas))
    test_th.start()
        
    root.mainloop()
