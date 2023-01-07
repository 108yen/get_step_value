import os
import pandas as pd
import xlwings as xw
import win32gui
import time
import ctypes
import pyautogui
import datetime


class RPA:
    def __init__(self) -> None:
        self.stocklist = pd.read_csv(
            'data/code_list.csv', header=0, encoding='cp932', dtype=str)
        codelist = self.stocklist['銘柄コード']

        self.wb = xw.Book()
        self.wb.app.api.RegisterXLL(
            r"C:/Users/kazuk/AppData/Local/MarketSpeed2/Bin/rss/MarketSpeed2_RSS_64bit.xll")
        self.wb.activate()
        self.sheet = self.wb.sheets.add()

        self.set_macro(self.sheet, codelist)
        self.wb.save('data/RSS_step_value_reader.xlsx')
        self.enable_RSS(self.sheet)

    
    def get_stocklist(self):
        return self.stocklist

    def get_sheet(self):
        return self.sheet

    def close_wb(self):
        self.wb.close()


 

    def set_macro(self,sheet, codelist):
        for index, code in enumerate(codelist):
            sheet.cells(2, 1+index*3).value = ["時刻", "出来高", "約定値"]
            sheet.cells(
                1, 1+index*3).value = "=@RssTickList(,\"" + code+".T\",100)"


    def enable_RSS(self,sheet):
        hwnd = win32gui.FindWindow(None, 'RSS_step_value_reader.xlsx - Excel')
        while not win32gui.IsWindowEnabled(hwnd):
            time.sleep(2)

        while sheet.cells(3, 1).value is None:
            print('RSS接続再試行')
            rect = win32gui.GetWindowRect(hwnd)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            pyautogui.click(rect[0]+1220, rect[1]+110)
            pyautogui.click(rect[0]+50, rect[1]+200)
            time.sleep(3)
        win32gui.ShowWindow(hwnd, 6)


if __name__ == '__main__':
    pass
