import time
import start_ex
import pandas as pd
from datetime import datetime
import schedule
from remove_duplicate_data import remove_duplicate
import os

# todo:非同期にする

CODE_LIST = ['9519', '9258', '9257', '9254', '9212', '9211', '9107',
             '7133', '7383', '7254',
             '6554', '6524', '6522',
             '5759',
             '4599', '4591', '4418', '4417', '4414', '4412', '4260', '4261', '4263', '4264', '4265', '4259', '4125', '4080',
             '2585', '2484', '2427', '2158']


def read_xlwings():
    app = start_ex.xw_apps_add_fixed()
    # app.visible = False
    wb = app.books.add()
    sheet = wb.sheets["Sheet1"]
    set_macro(sheet)
    try:
        get_step_value(sheet)
    except TypeError as e:
        print(e)
    wb.close()
    app.kill()


def set_macro(sheet):
    for index, code in enumerate(CODE_LIST):
        sheet.cells(2, 1+index*3).value = ["時刻", "出来高", "約定値"]
        sheet.cells(
            1, 1+index*3).value = "=@RssTickList(,\"" + code+".T\",100)"


def get_step_value(sheet):

    n = 0
    start_am = datetime.strptime("08:59:00", '%H:%M:%S').time()
    fin_am = datetime.strptime("11:30:30", '%H:%M:%S').time()
    start_pm = datetime.strptime("12:29:00", '%H:%M:%S').time()
    fin_pm = datetime.strptime("15:00:30", '%H:%M:%S').time()

    # dataframeを銘柄分作成（結構頭悪い処理）
    df_list = {}
    for code in CODE_LIST:
        df_list[code] = pd.DataFrame(columns=["時刻", "出来高", "約定値"])

    # 場中動く処理
    while start_am < datetime.today().time() < fin_pm:
        # while start_am < datetime.today().time() < fin_am or\
        #         start_pm < datetime.today().time() < fin_pm:
        time.sleep(0.1)
        # 銘柄ごとに動く処理
        for index, code in enumerate(CODE_LIST):
            # df_list[code] = df_list[code].append(pd.DataFrame(sheet.range((3, 1+index*3), (103, 3+index*3)).value, columns=[
            #     "時刻", "出来高", "約定値"]))
            df_list[code] = remove_duplicate(df_list[code],
                                             pd.DataFrame(sheet.range((3, 1+index*3), (103, 3+index*3)).value, columns=["時刻", "出来高", "約定値"]))

        n += 1
        if n % 1000 == 0:
            print("取得回数："+str(n))

    # 保存
    for code in CODE_LIST:
        df_list[code] = df_list[code].reset_index(drop=True)
        new_dir_path = 'data/'+datetime.today().strftime('%Y%m%d')
        os.makedirs(new_dir_path, exist_ok=True)
        fname = new_dir_path+'/'+code+'.csv'
        # fname = 'data/'+code+'_'+datetime.today().strftime('%Y%m%d_%H%M')+'.csv'
        df_list[code].to_csv(fname, encoding='cp932')
    print("保存完了")

    if datetime.today().time() >= fin_pm:
        exit()  # ほんとはここじゃない


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
    schedule.every().day.at("08:59").do(read_xlwings)
    # schedule.every().day.at("12:29").do(read_xlwings)
    while True:
        schedule.run_pending()
        time.sleep(10)
    # test()


if __name__ == '__main__':
    main()
