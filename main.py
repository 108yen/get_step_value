import openpyxl
import xlwings
import time
import get_data.start_ex as start_ex
import pandas as pd
from datetime import datetime

# todo：GUIでチャート作成


def read_openpyxl():
    # wb_w = openpyxl.load_workbook("Sample.xlsx")
    wb_w = openpyxl.Workbook()
    ws_w = wb_w.worksheets[0]
    ws_w["A1"].value = "=@RssTickList($A$2:$C$2,\"2929.T\",100)"
    ws_w["A2"].value = "時刻"
    ws_w["B2"].value = "出来高"
    ws_w["C2"].value = "約定値"
    ws_w["E4"].value = "=10+10"
    # ws = wb["Sheet"]
    # ws = wb.worksheets[0]
    print(ws_w["E4"].value)
    wb_w.save("Sample.xlsx")


def read_xlwings():
    # 非表示でExcelアプリを開く
    # app = xlwings.App(visible=True)
    app = start_ex.xw_apps_add_fixed()
    app.visible = False
    # wb = app.books.open("Sample.xlsx")
    wb = app.books.add()
    sheet = wb.sheets["Sheet1"]
    set_macro(sheet)
    try:
        get_step_value(sheet)
    except TypeError as e:
        print(e)
    # print(sheet.range('A1').value)
    # print(type(sheet.range('A2:C103').value))  # list
    # wb.save("Sample.xlsx")
    wb.close()
    app.kill()


def set_macro(sheet):
    sheet.range('A2').value = ["時刻", "出来高", "約定値"]
    sheet.range('A1').value = "=@RssTickList($A$2:$C$2,\"2929.T\",100)"


def get_step_value(sheet):
    n = 0
    duplicates_df = pd.DataFrame(columns=["時刻", "出来高", "約定値"])
    unique_df = pd.DataFrame(columns=["時刻", "出来高", "約定値"])
    while n < 3:
        time.sleep(1)
        n += 1
        # print(pd.DataFrame(sheet.range('A3:C103').value,
        #   columns=["時刻", "出来高", "約定値"]))
        # 落としちゃダメな時がある
        duplicates_df = pd.DataFrame(
            sheet.range('A3:C103').value, columns=["時刻", "出来高", "約定値"]).dropna(how='all')
        duplicates_df["時刻"] = duplicates_df.apply(
            lambda x: x if str(x['時刻']) == str('--------') else datetime.strptime(str(x['時刻']), '%H:%M:%S').time(), axis=1)
        # unique_df = duplicates_df.drop_duplicates().values
        if unique_df.empty:
            unique_df = duplicates_df
        elif str(duplicates_df[0:1]['約定値'].values) != str('--------'):
            duplicates_df[duplicates_df['時刻'] >= unique_df[0:1]['時刻']]
            if unique_df[0:1]['時刻'][0] > datetime.today().time():
                print('15時よりまえ')
            else:
                print('15時よりあと')
            print(unique_df[0:1]['時刻'][0])
    # print(duplicates_df)
    # print(unique_df)


def main():
    read_xlwings()


if __name__ == '__main__':
    main()
