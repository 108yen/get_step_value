import datetime
from logging import exception
import queue
import time
from matplotlib.pyplot import get
import pandas as pd
# import pywintypes
# import win32gui
# import win32con
# import win32process
# import pyautogui
from get_data import start_ex
from multiprocessing import Process
from multiprocessing import Queue
import os
import schedule
import ctypes
# import cudf
# from numba import cuda
import numpy as np
from sqlalchemy import create_engine
import mysql.connector
import glob
from tqdm import tqdm
import test_conf

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
    stocklist = pd.read_csv(
    'data/code_list.csv', header=0, encoding='cp932',dtype=str)
    codelist=stocklist['銘柄コード']
    q = Queue()
    p1 = Process(target=process_in, args=(q,codelist))
    p2 = Process(target=process2_out, args=(q,codelist))

    print('start')
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print('fin')
    exit()


def process_in(q,codelist):
    app, pid = start_ex.xw_apps_add_fixed()
    # app.visible = False
    # hwnds = get_hwnds_for_pid(pid)
    wb = app.books.add()
    sheet = wb.sheets["Sheet1"]
    for index, code in enumerate(codelist):
        sheet.cells(2, 1+index*3).value = ["時刻", "出来高", "約定値"]
        sheet.cells(
            1, 1+index*3).value = "=@RssTickList(,\"" + code+".T\",100)"
    wb.save('data/RSS_step_value_reader.xlsx')

    hwnd = win32gui.FindWindow(None, 'RSS_step_value_reader.xlsx - Excel')
    while sheet.cells(3, 1).value is None:
        print('RSS接続再試行')
        rect = win32gui.GetWindowRect(hwnd)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        pyautogui.click(rect[0]+1520, rect[1]+100)
        pyautogui.click(rect[0]+50, rect[1]+200)
        time.sleep(5)
    win32gui.ShowWindow(hwnd, 6)

    df_list = {}
    for code in codelist:
        df_list[code] = pd.DataFrame(columns=["時刻", "出来高", "約定値"])

    for i in range(10):
        for index, code in enumerate(codelist):
            df_list[code] = pd.DataFrame(sheet.range(
                (3, 1+index*3), (103, 3+index*3)).value, columns=["時刻", "出来高", "約定値"])

        q.put(df_list)
        # print('process1:'+str(i))
        # time.sleep(1)
    wb.close()
    app.kill()
    os.remove('data/RSS_step_value_reader.xlsx')


def process2_out(q,codelist):
    time.sleep(10)
    df_list = {}
    for code in codelist:
        df_list[code] = pd.DataFrame(columns=["時刻", "出来高", "約定値"])

    i = 0
    while True:
        try:
            # 取り出し
            get_df_list = q.get(block=True, timeout=3)
            # print('process2:'+str(i))
            print("\r残キュー数:"+str(q.qsize()), end="")
            i += 1
            # 銘柄ごとに動く処理
            for index, code in enumerate(codelist):
                df_list[code] = remove_duplicate(
                    df_list[code], get_df_list[code])
                # print(df_list)
        except queue.Empty:
            print('\nタイムアウト')
            break
        except Exception as e:
            print(e)

    for index, code in enumerate(codelist):
        df_list[code] = df_list[code].reset_index(drop=True)
        today_str = datetime.datetime.today().strftime('%Y%m%d')
        try:
            os.makedirs('data/test/'+today_str, exist_ok=True)
            df_list[code].to_csv('data/test/'+today_str +
                                 '/'+str(code)+'.csv', encoding='cp932')
        except Exception as e:
            print(code+':'+e)
    print('保存完了')


def while_test():
    while True:
        while False:
            print('i')
        else:
            break
    print('正常終了')


def schedule_test():
    schedule.every().day.at("17:03").do(multiprocess_test)
    while True:
        schedule.run_pending()
        time.sleep(10)


def save_codelist():
    codelist = ['9519', '9258', '9257', '9254', '9214', '9213', '9212', '9211', '9107', '9101', '9104',
                '7133', '7383', '7370', '7254',
                '6639', '6554', '6548', '6524', '6522',
                '5759',
                '4962', '4599', '4591', '4418', '4417', '4414', '4412', '4260', '4261', '4263', '4264', '4265', '4267', '4259', '4125', '4014', '4080',
                '3604', '3936',
                '2585', '2484', '2438', '2427', '2345', '2195', '2158']

    jpx_list = pd.read_csv(
        'data/jpx_list.csv', header=0, encoding='utf8')
    namelist = pd.DataFrame()
    # namelist=namelist.append(['test'])
    # namelist = namelist.append(['test2']).reset_index(drop=True).rename(columns={0:'銘柄名'})
    # print(namelist)
    for code in codelist:
        try:
            title = jpx_list[jpx_list['コード']
                             == int(code)]['銘柄名'].values[0]
        except IndexError:
            title = '銘柄リストにない銘柄コード'
        namelist = namelist.append([title])
    namelist = namelist.reset_index(
        drop=True).rename(columns={0: '銘柄名'})
    code_name_list = pd.concat(
        [pd.DataFrame(codelist, columns=['銘柄コード']), namelist],axis=1)
    # print(code_name_list)
    code_name_list.to_csv('data/code_list.csv', encoding='cp932')

def list_test():
    codelist = pd.read_csv(
        'data/code_list.csv', header=0,index_col=0, encoding='cp932')
    precodelist = ['9519', '9258', '9257', '9254', '9214', '9213', '9212', '9211', '9107', '9101', '9104',
                '7133', '7383', '7370', '7254',
                '6639', '6554', '6548', '6524', '6522',
                '5759',
                '4962', '4599', '4591', '4418', '4417', '4414', '4412', '4260', '4261', '4263', '4264', '4265', '4267', '4259', '4125', '4014', '4080',
                '3604', '3936',
                '2585', '2484', '2438', '2427', '2345', '2195', '2158']

    if precodelist:
        print('同じ')

def get_cwd():
    f = open('data/test_out.txt', 'a', encoding='cp932')
    f.write(os.getcwd())

def cuda_test():
    df = cudf.DataFrame()
    df['in1'] = np.arange(1000, dtype=np.float64)
    print(df)

def all_code_get_test():    #!500銘柄が限界
    stocklist = pd.read_csv(
    'data/all_code_list.csv', header=0, encoding='utf8',dtype=str)
    codelist=stocklist['銘柄コード']

    app, pid = start_ex.xw_apps_add_fixed()
    # app.visible = False
    # hwnds = get_hwnds_for_pid(pid)
    wb = app.books.add()
    sheet = wb.sheets["Sheet1"]
    for index, code in enumerate(codelist):
        sheet.cells(
                1+index, 1).value = "=@RssMarket(" + code+",\"歩み1詳細時刻\")"
        sheet.cells(
                1+index, 2).value = "=@RssMarket(" + code+",\"歩み1\")"
        sheet.cells(
                1+index, 3).value = "=@RssMarket(" + code+",\"出来高\")"
        # sheet.cells(1, 1+index*3).value = ["時刻", "出来高", "約定値"]
        # for i in range(1,5):
        #     sheet.cells(
        #         1+i, 1+index*3).value = "=@RSS|\'" + code+".T\'!歩み"+str(i)+"詳細時刻"
        # for i in range(1,5):
        #     sheet.cells(
        #         1+i, 3+index*3).value = "=@RSS|\'" + code+".T\'!歩み"+str(i)
    # wb.save('data/RSS_step_value_reader.xlsx')

    # hwnd = win32gui.FindWindow(None, 'RSS_step_value_reader.xlsx - Excel')
    # while sheet.cells(3, 1).value is None:
    #     print('RSS接続再試行')
    #     rect = win32gui.GetWindowRect(hwnd)
    #     ctypes.windll.user32.SetForegroundWindow(hwnd)
    #     pyautogui.click(rect[0]+1520, rect[1]+100)
    #     pyautogui.click(rect[0]+50, rect[1]+200)
    #     time.sleep(5)
    # win32gui.ShowWindow(hwnd, 6)

# 今までのデータをdbにぶち込んでみる
def dbtest():
    # engine = create_engine(
    #     'mysql+mysqlconnector://root:test@127.0.0.1/testsb')
    engine = create_engine(
        'mysql+mysqlconnector://'+test_conf.db_user+':'+test_conf.db_pass+'@'+test_conf.db_ip+'/stock')
    # df = pd.read_sql_query('SELECT * FROM codelist', con=engine)
    # print(df)

    # filelist = glob.glob('data/202202[12][0-9]')
    # filelist.extend(glob.glob('data/2022020[89]'))
    # print(filelist)
    filelist = glob.glob('data/202202[12][0-9]/*.csv')
    filelist.extend(glob.glob('data/2022020[89]/*.csv'))
    for filepath in tqdm(filelist):
        stepdf = pd.read_csv(filepath, header=0, index_col=0,
                                      encoding='cp932')
        stepdf.rename(columns={'時刻': 'time', '約定値': 'value',
                      '出来高': 'volume'}, inplace=True)
        datestr=filepath[5:13]
        stepdf['date']=datetime.date(int(datestr[:4]),int(datestr[4:6]),int(datestr[6:]))
        stepdf['dayindex']=stepdf.index
        stepdf['code']=int(filepath[14:18])
        to_time=lambda x:datetime.time(int(x[:2]),int(x[3:5]),int(x[6:8]))
        stepdf['time']=stepdf['time'].apply(to_time)
        try:
            stepdf.to_sql('step', engine, if_exists='append', index=None)
        except Exception as e:
            f = open('data/test_out.txt', 'a', encoding='cp932')
            f.write(e)


    # 差分表示用
    # stocklist = pd.read_csv(
    #     'data/code_list.csv', header=0, encoding='cp932', dtype=str)
    # codelist = stocklist['銘柄コード']
    # s=set()
    # for day in ['20220225', '20220224', '20220222', '20220221', '20220218']:
    #     for filename in glob.glob('data/'+day+'/*csv'):
    #         if not filename.split('/')[2][:4] in codelist.values:
    #             s.add(filename.split('/')[2][:4])
                
    # print(s)
def db_search_test():
    engine = create_engine(
        'mysql+mysqlconnector://'+test_conf.db_user+':'+test_conf.db_pass+'@'+test_conf.db_ip+'/stock')
    get_df = pd.read_sql_query('SELECT code FROM step WHERE (`date` IN (\'2022-02-28\')) AND (dayindex IN (0))', con=engine)
    codelist_df=pd.read_sql_query('SELECT * FROM codelist', con=engine)
    out_df=pd.DataFrame(columns=["code","name"])
    for code in codelist_df['code']:
        if not code in get_df.values:
            out_df=pd.concat([out_df,codelist_df[codelist_df['code']==code]], ignore_index=True)
    print(out_df)
# todo:codelistに全銘柄リストぶち込みたい
# todo:取得日付とかもDBで管理できるとよい？

def db_priv_test():
    # test_df=pd.DataFrame(np.arange(12).reshape(3, 4),
    #               columns=['col_0', 'col_1', 'col_2', 'col_3'],
    #               index=['row_0', 'row_1', 'row_2'])
    engine = create_engine(
        'mysql+mysqlconnector://'+test_conf.db_user+':'+test_conf.db_pass+'@'+test_conf.db_ip+'/stock')
    try:
        # test_df.to_sql('test', engine, if_exists='append', index=None)
        print(pd.read_sql_query('SELECT concat(cast(date as char),\' \',cast(time as char)) AS datetime,volume,value FROM step WHERE date=\'2022-03-02\' AND code=2158 ORDER BY dayindex ASC', \
            con=engine,\
                parse_dates={'datetime':'%Y-%m-%d %H:%M:%S'}
            )['datetime'][:1])
    except Exception as e:
        print(e)

def db_input_getday():
    filelist = glob.glob('data/202202[12][0-9]/*.csv')
    filelist.extend(glob.glob('data/2022020[89]/*.csv'))
    filelist.extend(glob.glob('data/202203[0-9][0-9]/*.csv'))

    engine = create_engine(
        'mysql+mysqlconnector://'+test_conf.db_user+':'+test_conf.db_pass+'@'+test_conf.db_ip+'/stock')
    getdate_df = pd.DataFrame(columns=['date','code'])
    for filepath in filelist:
        split_path=filepath.split('\\')
        getdate=datetime.date(int(split_path[1][0:4]),int(split_path[1][4:6]),int(split_path[1][6:8]))
        code=split_path[2].split('.')[0]
        getdate_df=pd.concat([getdate_df,pd.DataFrame([[getdate,code]],columns=['date','code'])], ignore_index=True)
    # print(getdate_df)
    getdate_df.to_sql('getdate', engine, if_exists='append', index=None)

def convert_test():
    stocklist = pd.read_csv(
        'data/code_list.csv', header=0, encoding='cp932', dtype=str)
    # codelist = stocklist[['銘柄コード']].astype('int')
    codelist = stocklist['銘柄コード']
    getlist_df=pd.DataFrame({'code':codelist})
    getlist_df['code']=getlist_df['code'].astype('int')
    # codelist.rename(columns={'銘柄コード':'code'}, inplace=True)
    getlist_df['date']=datetime.date.today()
    print(getlist_df.dtypes)

def forgot_data():
    engine = create_engine(
        'mysql+mysqlconnector://'+test_conf.db_user+':'+test_conf.db_pass+'@'+test_conf.db_ip+'/stock')
    # filepath='data/20220330/9219.csv'
    # stepdf = pd.read_csv(filepath, header=0, index_col=0,
    #                                 encoding='cp932')
    # stepdf.rename(columns={'時刻': 'time', '約定値': 'value',
    #                 '出来高': 'volume'}, inplace=True)
    # datestr=filepath[5:13]
    # stepdf['date']=datetime.date(int(datestr[:4]),int(datestr[4:6]),int(datestr[6:]))
    # stepdf['dayindex']=stepdf.index
    # stepdf['code']=int(filepath[14:18])
    # to_time=lambda x:datetime.time(int(x[:2]),int(x[3:5]),int(x[6:8]))
    # stepdf['time']=stepdf['time'].apply(to_time)
    # try:
    #     stepdf.to_sql('step', engine, if_exists='append', index=None)
    # except Exception as e:
    #     f = open('data/test_out.txt', 'a', encoding='cp932')
    #     f.write(e)
    
    stocklist = pd.read_csv(
        'data/code_list.csv', header=0, encoding='cp932', dtype=str)
    codelist = stocklist['銘柄コード']
    getlist_df=pd.DataFrame({'code':codelist})
    getlist_df['code']=getlist_df['code'].astype('int')
    getlist_df['date']=datetime.date.today()
    getlist_df.to_sql('getdate', engine, if_exists='append', index=None)
    print('db送信完了')

def analysys_sakureisu():
    engine = create_engine(
        'mysql+mysqlconnector://'+test_conf.db_user+':'+test_conf.db_pass+'@'+test_conf.db_ip+'/stock')
    get_df = pd.read_sql_query('SELECT concat(cast(date as char),\' \',cast(time as char)) AS datetime,value,volume FROM step WHERE (`date` IN (\'2022-04-15\')) AND (code=5029) ORDER BY dayindex ASC', \
        con=engine, parse_dates={'datetime':'%Y-%m-%d %H:%M:%S'})
    get_df['trading_price']=get_df['value']*get_df['volume']
    # df_sum=get_df[get_df['datetime']<datetime.datetime(2022,4,15,9,15)].sum()
    tmp_df=get_df[datetime.datetime(2022,4,15,13,10)<get_df['datetime']]
    df_sum=tmp_df[tmp_df['datetime']<datetime.datetime(2022,4,15,13,25)].sum()
    print(df_sum['volume'])

    # sum_volume=0
    # for index,data in get_df.iloc[::-1].iterrows():
    #     # print(data)
    #     sum_volume+=data['volume']
    #     if sum_volume>8200000:
    #         print(data['datetime'])
    #         break

if __name__ == '__main__':
    # main()
    # rpa_test()
    # multiprocess_test()
    # while_test()
    # schedule_test()
    # save_codelist()
    # list_test()
    # get_cwd()
    # cuda_test()
    # all_code_get_test()
    # dbtest()
    # db_search_test()
    # db_priv_test()
    # db_input_getday()
    # convert_test()
    # forgot_data()
    analysys_sakureisu()