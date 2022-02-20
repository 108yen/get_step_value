from matplotlib.pyplot import connect
from ..get_data import start_ex
import pywintypes
import win32gui
import win32con
import ctypes
import pyautogui
import time

# todo:データ取得してくれるやつ
# todo:あるデータから補完してくれるやつ
# todo:convasに表示してくれるやつ

class Dailychart():
    def __init__(self):
    # エクセル開いたりする処理
        app, pid = start_ex.xw_apps_add_fixed()
        # app.visible = False
        wb = app.books.add()
        sheet = wb.sheets["Sheet1"]
        self.set_macro(sheet, codelist)
        wb.save('data/RSS_dailychart_reader.xlsx')
        self.connect_excelRSS(sheet)

    def get_dailychart():
        print()
    
    def set_macro(sheet, codelist):
        for index, code in enumerate(codelist):
            sheet.cells(2, 1+index*3).value = ["時刻", "出来高", "約定値"]
            sheet.cells(
                1, 1+index*3).value = "=@RssTickList(,\"" + code+".T\",100)"

    def connect_excelRSS(self,sheet):
        hwnd = win32gui.FindWindow(None, 'RSS_dailychart_reader.xlsx - Excel')
        while sheet.cells(3, 1).value is None:
            print('RSS接続再試行')
            rect = win32gui.GetWindowRect(hwnd)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            pyautogui.click(rect[0]+1520, rect[1]+100)
            pyautogui.click(rect[0]+50, rect[1]+200)
            time.sleep(3)
        win32gui.ShowWindow(hwnd, 6)

    def complement_data():
        print()

    def draw_canvas():
        print()

if __name__ == '__main__':
    Dailychart()