import queue
from multiprocessing import Queue
from multiprocessing import Process
import time
import start_ex
from get_hwnds_for_pid import get_hwnds_for_pid
import pandas as pd
import datetime
import schedule
from remove_duplicate_data import remove_duplicate
import os
import pywintypes
import win32gui
import pyautogui
import ctypes
import jpholiday
from sqlalchemy import create_engine
import mysql.connector
from tqdm import tqdm
import db_conf


class Oliginal_Holiday(jpholiday.OriginalHoliday):
    def _is_holiday(self, DATE):
        if DATE == datetime.date(2022, 1, 3):
            return True
        return False

    def _is_holiday_name(self, date):
        return '特別休暇'

def read_xlwings():
    if not jpholiday.is_holiday(datetime.date.today()):
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
    start_am = datetime.datetime.strptime("08:59:00", '%H:%M:%S').time()
    fin_am = datetime.datetime.strptime("11:30:30", '%H:%M:%S').time()
    start_pm = datetime.datetime.strptime("12:20:00", '%H:%M:%S').time()
    fin_pm = datetime.datetime.strptime("15:00:30", '%H:%M:%S').time()

    # dataframeを銘柄分作成（結構頭悪い処理）
    df_list = {}
    for code in codelist:
        df_list[code] = pd.DataFrame(columns=["時刻", "出来高", "約定値"])

    # 時間まで待ち
    while datetime.datetime.today().time() < start_am:
        time.sleep(10)

    # 場中動く処理
    while start_am < datetime.datetime.today().time() < fin_pm:
        # 昼休憩
        if fin_am < datetime.datetime.today().time() < start_pm:
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
    start_am = datetime.datetime.strptime("08:59:00", '%H:%M:%S').time()
    fin_am = datetime.datetime.strptime("11:30:30", '%H:%M:%S').time()
    start_pm = datetime.datetime.strptime("12:20:00", '%H:%M:%S').time()
    fin_pm = datetime.datetime.strptime("15:00:30", '%H:%M:%S').time()
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
            if datetime.datetime.today().time() > fin_pm:
                print('処理終了')
                break
        except Exception as e:
            print(e)

    save_data(df_list, codelist)


def save_data(data, codelist):
    # 歩みね保存
    today_str = datetime.datetime.today().strftime('%Y%m%d')
    for code in tqdm(codelist):
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
    print('csv保存完了')

    # raspidbに送る処理
    try:
        engine = create_engine(
            'mysql+mysqlconnector://'+db_conf.db_user+':'+db_conf.db_pass+'@'+db_conf.db_ip+'/stock')
    except Exception as e:
        print(e)
        f = open('data/test_out.txt', 'a', encoding='cp932')
        f.write(e)
        f.close()

    for code in tqdm(codelist):
        stepdf = data[code].reset_index(drop=True)
        stepdf.rename(columns={'時刻': 'time', '約定値': 'value',
                      '出来高': 'volume'}, inplace=True)
        stepdf['date']=datetime.date.today()
        stepdf['dayindex']=stepdf.index
        stepdf['code']=int(code)
        to_time=lambda x:datetime.time(int(x[:2]),int(x[3:5]),int(x[6:8]))
        stepdf['time']=stepdf['time'].apply(to_time)
        try:
            stepdf.to_sql('step', engine, if_exists='append', index=None)
        except Exception as e:
            f = open('data/test_out.txt', 'a', encoding='cp932')
            f.write('error:'+code)
            f.write(e)
            f.close()

    # 今日取得した銘柄を記録
    getlist_df=pd.DataFrame({'code':codelist})
    getlist_df['code']=getlist_df['code'].astype('int')
    getlist_df['date']=datetime.date.today()
    getlist_df.to_sql('getdate', engine, if_exists='append', index=None)
    print('db送信完了')

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

    # print("保存完了")

def main():
    try:
        read_xlwings()
    except Exception as e:
        f = open('data/log.txt', 'a', encoding='cp932')
        f.write(e)


if __name__ == '__main__':
    main()
