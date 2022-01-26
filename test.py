import pandas as pd
import win32gui
import win32con
import win32process
from get_data import start_ex


def rpa_test():
    app,pid = start_ex.xw_apps_add_fixed()
    wb = app.books.add()
    sheet = wb.sheets["Sheet1"]
    print(app)
    hwnds=get_hwnds_for_pid(pid)
    # p_handle = win32gui.FindWindow(None, "Excel")
    print(hwnds)
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
    codename_list = pd.read_csv(fname, header=0,encoding='utf8')
    try:
        print(codename_list[codename_list['コード']==73]['銘柄名'].values[0])
    except IndexError:
        print('エラー') 

if __name__ == '__main__':
    # main()
    # rpa_test()
    win32gui.SetForegroundWindow(0x619fc)
    win32gui.SendMessage(0x619fc, win32con.WM_CAPTURECHANGED)
    win32gui.SendMessage(0x619fc, win32con.BM_CLICK, 0x1, 0x41000f)
    # win32gui.SendMessage(0x619fc, win32con.WM_LBUTTONDOWN, 0x1, 0x41000f)
    # win32gui.SendMessage(0x619fc, win32con.WM_LBUTTONUP, 0, 0x1000f)
