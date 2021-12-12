import openpyxl
import xlwings
import time
import start_ex
import pandas as pd
from datetime import datetime
import schedule


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
    sheet.range('A1').value = "=@RssTickList($A$2:$C$2,\"2929.T\",100)"


def get_step_value(sheet):
    duplicates_df = pd.DataFrame(columns=["時刻", "出来高", "約定値"])
    n = 0
    while datetime.today().time() < datetime.strptime("11:30:00", '%H:%M:%S').time():
        time.sleep(1)
        duplicates_df = duplicates_df.append(pd.DataFrame(sheet.range('A3:C103').value, columns=[
            "時刻", "出来高", "約定値"]))
        n += 1
        print("取得回数："+str(n))

    duplicates_df.to_csv('row_data.csv', encoding='cp932')
    print("保存完了")
    exit()


def main():
    schedule.every().day.at("09:00").do(read_xlwings)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
