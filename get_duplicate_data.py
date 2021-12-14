import openpyxl
import xlwings
import time
import start_ex
import pandas as pd
from datetime import datetime
import schedule

CODE = '6554'


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
    sheet.range('A2').value = ["時刻", "出来高", "約定値"]
    sheet.range('A1').value = "=@RssTickList($A$2:$C$2,\""+CODE+".T\",100)"


def get_step_value(sheet):
    duplicates_df = pd.DataFrame(columns=["時刻", "出来高", "約定値"])
    n = 0
    start_am = datetime.strptime("08:59:00", '%H:%M:%S').time()
    fin_am = datetime.strptime("11:30:30", '%H:%M:%S').time()
    start_pm = datetime.strptime("12:29:00", '%H:%M:%S').time()
    fin_pm = datetime.strptime("15:00:30", '%H:%M:%S').time()
    while start_am < datetime.today().time() < fin_am or\
            start_pm < datetime.today().time() < fin_pm:
        time.sleep(1)
        duplicates_df = duplicates_df.append(pd.DataFrame(sheet.range('A3:C103').value, columns=[
            "時刻", "出来高", "約定値"]))
        n += 1
        print("取得回数："+str(n))

    duplicates_df = duplicates_df.reset_index(drop=True)
    fname = 'data/'+CODE+'_'+datetime.today().strftime('%Y%m%d_%H%M')+'.csv'
    duplicates_df.to_csv(fname, encoding='cp932')
    print("保存完了")

    if datetime.today().time() >= fin_pm:
        exit()  # ほんとはここじゃない


def main():
    schedule.every().day.at("08:59").do(read_xlwings)
    schedule.every().day.at("12:29").do(read_xlwings)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
