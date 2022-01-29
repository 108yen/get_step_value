from logging import exception
import queue
import time
import pandas as pd
import win32gui
import win32con
import win32process
import pyautogui
from get_data import start_ex
from multiprocessing import Process
from multiprocessing import Queue
import os

from get_data.remove_duplicate_data import remove_duplicate

CODE_LIST = ['9519', '9258', '9257', '9254', '9212', '9211', '9107',
             '7133', '7383', '7370', '7254',
             '6554', '6524', '6522',
             '5759',
             '4599', '4591', '4418', '4417', '4414', '4412', '4260', '4261', '4263', '4264', '4265', '4259', '4125', '4080',
             '3604',
             '2585', '2484', '2427', '2345', '2158']

def rpa_test():
    app, pid = start_ex.xw_apps_add_fixed()
    wb = app.books.add()
    sheet = wb.sheets["Sheet1"]
    hwnds = get_hwnds_for_pid(pid)
    rect = win32gui.GetWindowRect(hwnds[0])
    print(rect)
    pyautogui.click(rect[0]+1520, rect[1]+100)
    pyautogui.click(rect[0]+50, rect[1]+200)

    # app.kill()


def get_hwnds_for_pid(pid):
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


def main():
    fname = 'data/code_list.csv'
    codename_list = pd.read_csv(fname, header=0, encoding='utf8')
    try:
        print(codename_list[codename_list['コード'] == 73]['銘柄名'].values[0])
    except IndexError:
        print('エラー')


def multiprocess_test():
    q = Queue()
    p1 = Process(target=process_in, args=(q,))
    p2 = Process(target=process2_out, args=(q,))

    print('start')
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print('fin')


def process_in(q):
    app, pid = start_ex.xw_apps_add_fixed()
    # app.visible = False
    hwnds = get_hwnds_for_pid(pid)
    rect = win32gui.GetWindowRect(hwnds[0])
    wb = app.books.add()
    sheet = wb.sheets["Sheet1"]
    for index, code in enumerate(CODE_LIST):
        sheet.cells(2, 1+index*3).value = ["時刻", "出来高", "約定値"]
        sheet.cells(
            1, 1+index*3).value = "=@RssTickList(,\"" + code+".T\",100)"
    while sheet.cells(3, 1).value is None:
        print('RSS接続再試行')
        win32gui.SetForegroundWindow(hwnds[0])
        pyautogui.click(rect[0]+1520, rect[1]+100)
        pyautogui.click(rect[0]+50, rect[1]+200)
        time.sleep(1)

    df_list = {}
    for code in CODE_LIST:
        df_list[code] = pd.DataFrame(columns=["時刻", "出来高", "約定値"])

    for i in range(100):
        for index, code in enumerate(CODE_LIST):
            df_list[code] = pd.DataFrame(sheet.range(
                (3, 1+index*3), (103, 3+index*3)).value, columns=["時刻", "出来高", "約定値"])

        q.put(df_list)
        # print('process1:'+str(i))
        # time.sleep(1)
    wb.close()
    app.kill()


def process2_out(q):
    time.sleep(5)
    df_list = {}
    for code in CODE_LIST:
        df_list[code] = pd.DataFrame(columns=["時刻", "出来高", "約定値"])

    i=0
    while True:
        try:
            # 取り出し
            get_df_list = q.get(block=True, timeout=3)
            # print('process2:'+str(i))
            print("\r残キュー数:"+str(q.qsize()), end="")
            i+=1
            # 銘柄ごとに動く処理
            for index, code in enumerate(CODE_LIST):
                df_list[code] = remove_duplicate(
                    df_list[code], get_df_list[code])
                # print(df_list)
        except queue.Empty:
            print('\nタイムアウト')
            break
        except Exception as e:
            print(e)

    for index, code in enumerate(CODE_LIST):
        df_list[code] = df_list[code].reset_index(drop=True)
        try:
            os.makedirs('data/test/20220129', exist_ok=True)
            df_list[code].to_csv('data/test/20220129/'+str(code)+'.csv', encoding='cp932')
        except Exception as e:
            print(code+':'+e)

def while_test():
    while True:
        while False:
            print('i')
        else:
            break
    print('正常終了')

if __name__ == '__main__':
    # main()
    # rpa_test()
    multiprocess_test()
    # while_test()
