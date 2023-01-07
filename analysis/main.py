import os
import pandas as pd
import xlwings as xw
import win32gui
import time
import ctypes
import pyautogui
import datetime
from main_window import MainWindow
from big_trade import BigTrade
from rpa import RPA

if __name__ == '__main__':
    mainWindow=MainWindow()
    rpa=RPA()
    bigTrade=BigTrade(rpa.get_stocklist(),rpa.get_sheet())
    bigTrade.start()
    mainWindow.start_mainloop()

    bigTrade.join()
    rpa.close_wb()
