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
    for i in range(4):
        q.put(i)
        print('process1:'+str(i))
        time.sleep(1)


def process2_out(q):
    time.sleep(3)
    while True:
        try:
            out = q.get(block=True, timeout=3)
            print('process2:'+str(out))
        except queue.Empty:
            print('タイムアウト')
            break
        except Exception as e:
            print(e)


if __name__ == '__main__':
    # main()
    rpa_test()
    # multiprocess_test()
