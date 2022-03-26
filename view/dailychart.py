from matplotlib.pyplot import connect
import start_ex
import win32gui
import datetime
import win32con
import ctypes
import time
import os
# import pyautogui

# todo:データ取得してくれるやつ
# todo:あるデータから補完してくれるやつ
# todo:convasに表示してくれるやつ

class Dailychart():
    # def __init__(self):
    # # エクセル開いたりする処理
    #     app, pid = start_ex.xw_apps_add_fixed()
    #     # app.visible = False
    #     wb = app.books.add()
    #     sheet = wb.sheets["Sheet1"]
    #     self.set_macro(sheet, codelist)
    #     wb.save('data/RSS_dailychart_reader.xlsx')
    #     self.connect_excelRSS(sheet)
    
    # def set_macro(sheet, codelist):
    #     for index, code in enumerate(codelist):
    #         sheet.cells(2, 1+index*3).value = ["時刻", "出来高", "約定値"]
    #         sheet.cells(
    #             1, 1+index*3).value = "=@RssTickList(,\"" + code+".T\",100)"

    # def connect_excelRSS(self,sheet):
    #     hwnd = win32gui.FindWindow(None, 'RSS_dailychart_reader.xlsx - Excel')
    #     while sheet.cells(3, 1).value is None:
    #         print('RSS接続再試行')
    #         rect = win32gui.GetWindowRect(hwnd)
    #         ctypes.windll.user32.SetForegroundWindow(hwnd)
    #         pyautogui.click(rect[0]+1520, rect[1]+100)
    #         pyautogui.click(rect[0]+50, rect[1]+200)
    #         time.sleep(3)
    #     win32gui.ShowWindow(hwnd, 6)

    def is_exist_dailydata(self,code,date):
        print('bool')

    def get_dailydata(self,code,date):
    # エクセル開いたりする処理
        app, pid = start_ex.xw_apps_add_fixed()
        # app.visible = False
        wb = app.books.open('data/RSS_dailychart_reader.xlsx')
        sheet = wb.sheets["Sheet1"]
        target_date=datetime.date(int(date[:4]),int(date[4:6]),int(date[6:]))
        bg_date=target_date-datetime.timedelta(days=40)
        sheet.cells(1, 1).value = "=@RssChartPast(,\"" + code+".T\",\"D\",\""+bg_date.strftime("%Y%m%d")+"\",30)"
        wb.save('data/RSS_dailychart_reader.xlsx')
        hwnd = app.hwnd
        # while sheet.cells(3, 1).value is None:
        #     print('RSS接続再試行')
        #     rect = win32gui.GetWindowRect(hwnd)
        #     ctypes.windll.user32.SetForegroundWindow(hwnd)
        #     pyautogui.click(rect[0]+1520, rect[1]+100)
        #     pyautogui.click(rect[0]+50, rect[1]+200)
        #     time.sleep(3)
        # win32gui.ShowWindow(hwnd, 6)
        time.sleep(10)
        wb.close()
        app.kill()
        # os.remove('data/RSS_dailychart_reader.xlsx')

    def save_todb(dailydata):
        print()

    def draw_canvas():
        print()

if __name__ == '__main__':
    dailychart=Dailychart()
    dailychart.get_dailydata("2929","20220325")