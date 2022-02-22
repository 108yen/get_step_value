import queue
from multiprocessing import Queue
from multiprocessing import Process
import time
import start_ex
from get_hwnds_for_pid import get_hwnds_for_pid
import pandas as pd
from datetime import datetime
from datetime import date
import schedule
from remove_duplicate_data import remove_duplicate
import os
import pywintypes
import win32gui
import pyautogui
import ctypes
import jpholiday

class Oliginal_Holiday(jpholiday.OriginalHoliday):
    def _is_holiday(self, DATE):
        if DATE == date(2022, 1, 3):
            return True
        return False

    def _is_holiday_name(self, date):
        return '特別休暇'

def read_xlwings():
    if not jpholiday.is_holiday(date.today()):
        stocklist = pd.read_csv(
            'data/code_list.csv', header=0, encoding='cp932', dtype=str)
        codelist = stocklist['銘柄コード']

        q = Queue()
        p1 = Process(target=get_step_value, args=(q, codelist))
        p2 = Process(target=remove_dupulicate_p, args=(q, codelist))
        # get_step_value(sheet)
        p1.start()
        p2.start()
        p1.join()
        print('\np1終了')
        p2.join()
        print('p2終了')
        exit()


def set_macro(sheet, codelist):
    for index, code in enumerate(codelist):
        sheet.cells(2, 1+index*3).value = ["時刻", "出来高", "約定値"]
        sheet.cells(
            1, 1+index*3).value = "=@RssTickList(,\"" + code+".T\",100)"


def get_step_value(q, codelist):
    # エクセル開いたりする処理
    app, pid = start_ex.xw_apps_add_fixed()
    # app.visible = False
    wb = app.books.add()
    sheet = wb.sheets["Sheet1"]
    set_macro(sheet, codelist)
    wb.save('data/RSS_step_value_reader.xlsx')

    hwnd = win32gui.FindWindow(None, 'RSS_step_value_reader.xlsx - Excel')
    while sheet.cells(3, 1).value is None:
        print('RSS接続再試行')
        rect = win32gui.GetWindowRect(hwnd)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        pyautogui.click(rect[0]+1520, rect[1]+100)
        pyautogui.click(rect[0]+50, rect[1]+200)
        time.sleep(3)
    win32gui.ShowWindow(hwnd, 6)

    # n = 0
    start_am = datetime.strptime("08:59:00", '%H:%M:%S').time()
    fin_am = datetime.strptime("11:30:30", '%H:%M:%S').time()
    start_pm = datetime.strptime("12:20:00", '%H:%M:%S').time()
    fin_pm = datetime.strptime("15:00:30", '%H:%M:%S').time()

    # dataframeを銘柄分作成（結構頭悪い処理）
    df_list = {}
    for code in codelist:
        df_list[code] = pd.DataFrame(columns=["時刻", "出来高", "約定値"])

    # 時間まで待ち
    while datetime.today().time() < start_am:
        time.sleep(10)

    # 場中動く処理
    while start_am < datetime.today().time() < fin_pm:
        # 昼休憩
        if fin_am < datetime.today().time() < start_pm:
            print('\nヌーン')
            time.sleep(3000)
            print('\nぬーん終わり')
        time.sleep(0.5)
        # 銘柄ごとに動く処理
        for index, code in enumerate(codelist):
            df_list[code] = pd.DataFrame(sheet.range(
                (3, 1+index*3), (103, 3+index*3)).value, columns=["時刻", "出来高", "約定値"])
        # 何も処理せずまとめてキューにぶち込む
        q.put(df_list)

        # n += 1
        # if n % 1000 == 0:
        #     print("取得回数："+str(n))

    wb.close()
    app.kill()
    os.remove('data/RSS_step_value_reader.xlsx')


def remove_dupulicate_p(q, codelist):
    # Excel起動するまで待ち
    time.sleep(10)
    # 節目の時間
    start_am = datetime.strptime("08:59:00", '%H:%M:%S').time()
    fin_am = datetime.strptime("11:30:30", '%H:%M:%S').time()
    start_pm = datetime.strptime("12:20:00", '%H:%M:%S').time()
    fin_pm = datetime.strptime("15:00:30", '%H:%M:%S').time()
    # dataframeを銘柄分作成（結構頭悪い処理）
    df_list = {}
    for code in codelist:
        df_list[code] = pd.DataFrame(columns=["時刻", "出来高", "約定値"])

    n = 0
    while True:
        try:
            # 取り出し
            get_df_list = q.get(block=True, timeout=10)
            n += 1
            print("\r残キュー数:"+str(q.qsize())+" 回数:"+str(n)+"   ", end="")
            # 銘柄ごとに動く処理
            for index, code in enumerate(codelist):
                df_list[code] = remove_duplicate(
                    df_list[code], get_df_list[code])
        except queue.Empty:
            # print('\nタイムアウト')
            # ひけてたら終了
            if datetime.today().time() > fin_pm:
                print('処理終了')
                break
        except Exception as e:
            print(e)

    save_data(df_list, codelist)


def save_data(data, codelist):
    # 歩みね保存
    today_str = datetime.today().strftime('%Y%m%d')
    for code in codelist:
        data[code] = data[code].reset_index(drop=True)
        new_dir_path = 'data/'+today_str
        fname = new_dir_path+'/'+code+'.csv'
        if os.path.isfile(fname):
            fname = new_dir_path+'/_'+code+'.csv'
        try:
            os.makedirs(new_dir_path, exist_ok=True)
            data[code].to_csv(fname, encoding='cp932')
        except Exception as e:
            print(code+':'+e)
    # 5分足データの保存
    # for code in CODE_LIST:
    #     new_dir_path = 'data/'+today_str+'/5min'
    #     os.makedirs(new_dir_path, exist_ok=True)
    #     fname = new_dir_path+'/'+code+'.csv'
    #     # わざわざファイル読んでるの効率悪い
    #     try:
    #         split_five_min_data(code, today_str).to_csv(
    #             fname, encoding='cp932')
    #     except (FileNotFoundError, FileExistsError) as e:
    #         print(code+e)

    print("保存完了")


def test():
    # test = np.zeros((len(CODE_LIST), 1, 3))
    # print(test)
    # test[0, :, :] = np.append(test[0, :, :], [[1, 1, 1]], axis=0)
    # print(test)
    app = start_ex.xw_apps_add_fixed()
    # app.visible = False
    wb = app.books.add()
    sheet = wb.sheets["Sheet1"]
    set_macro(sheet)  # dataframeを銘柄分作成（結構頭悪い処理）
    df_list = {}
    for code in CODE_LIST:
        df_list[code] = pd.DataFrame(columns=["時刻", "出来高", "約定値"])

    # # 場中動く処理
    # while start_am < datetime.today().time() < fin_am or\
    #         start_pm < datetime.today().time() < fin_pm:
    time.sleep(1)
    # 銘柄ごとに動く処理
    for index, code in enumerate(CODE_LIST):
        df_list[code] = df_list[code].append(pd.DataFrame(sheet.range((3, 1+index*3), (103, 3+index*3)).value, columns=[
            "時刻", "出来高", "約定値"]))
    # duplicates_df = duplicates_df.append(pd.DataFrame(sheet.range('A3:C103').value, columns=[
    #     "時刻", "出来高", "約定値"]))

    # 保存
    for code in CODE_LIST:
        df_list[code] = df_list[code].reset_index(drop=True)
        fname = 'data/test/'+code+'_'+datetime.today().strftime('%Y%m%d_%H%M')+'.csv'
        df_list[code].to_csv(fname, encoding='cp932')
    # duplicates_df = duplicates_df.reset_index(drop=True)
    # fname = 'data/'+CODE_LIST+'_'+datetime.today().strftime('%Y%m%d_%H%M')+'.csv'
    # duplicates_df.to_csv(fname, encoding='cp932')
    print("保存完了")


def main():
    # schedule.every().day.at("08:59").do(read_xlwings)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(10)
    try:
        read_xlwings()
    except Exception as e:
        f = open('data/log.txt', 'a', encoding='cp932')
        f.write(e)


if __name__ == '__main__':
    main()
