import os
import pandas as pd
import xlwings as xw
import win32gui
import time
import ctypes
import pyautogui
import datetime


class BigTrade:
    def __init__(self, stocklist, sheet: xw.Sheet) -> None:
        self.bigTradeList = {}
        self.stocklist = stocklist
        self.codelist = stocklist['銘柄コード']
        self.sheet: xw.Sheet = sheet

        for code in self.codelist:
            self.bigTradeList[code] = pd.DataFrame(
                columns=["time", "trading_value", "isBuy"])

    def get_RSS_data(self,sheet):
        self.sheet=sheet
        # self.sheet=sheet
        for index, code in enumerate(self.codelist):
            try:
                RSS_data = pd.DataFrame(self.sheet.range(
                (3, 1+index*3), (103, 3+index*3)).value, columns=["time", "volume", "value"])
            except Exception as e:
                print(e)
                return
                
            # 計算のため、余計なデータ削除
            RSS_data = RSS_data[RSS_data['time'] != '--------'].dropna()
            RSS_data['trading_value'] = RSS_data['volume']*RSS_data['value']
            # print(RSS_data)
            big_trade = self.filter_big_trade(RSS_data)
            # print(big_trade)
            self.bigTradeList[code] = pd.concat(
                [self.bigTradeList[code], big_trade]).drop_duplicates()

    def print_tradingvalue(self):
        os.system('cls')
        for index, code in enumerate(self.codelist):
            # 5分間抽出
            fivemin_delay = datetime.datetime.now()-datetime.timedelta(minutes=5)
            recent_trade = self.bigTradeList[code][self.bigTradeList[code]
                                                   ['time'] > fivemin_delay.strftime('%H:%M:%S')]

            if len(recent_trade) != 0:
                symbol_info = stocklist[stocklist['銘柄コード'] == code].iloc[0]
                # 銘柄情報
                print('\n'+symbol_info['銘柄コード']+' '+symbol_info['銘柄名'])
                # 大人買い情報
                print(recent_trade)

    # RSS_data=pd.DataFrame(columns = ["time", "volume", "value", "trading_value"])

    def filter_big_trade(self, RSS_data) -> pd.DataFrame:
        reverse_RSS_data = RSS_data.iloc[::-1].reset_index(drop=True)
        result = pd.DataFrame()

        if len(reverse_RSS_data)==0:
            return result

        time = reverse_RSS_data.loc[0, 'time']
        value = reverse_RSS_data.loc[0, 'value']
        isBuy = True
        sum_tradingvalue = 0
        for index, item in reverse_RSS_data.iterrows():

            if item['value'] > value and isBuy:
                # print('買い')
                sum_tradingvalue += item['trading_value']
            elif item['value'] < value and not isBuy:
                # print('売り')
                sum_tradingvalue += item['trading_value']
            else:
                # print('初期化')
                if sum_tradingvalue > 8000000:
                    add_df = pd.DataFrame([[time, sum_tradingvalue, isBuy]],
                                          columns=["time", "trading_value", "isBuy"])
                    result = pd.concat([result, add_df], axis=0)
                # 初期化
                time = item['time']
                sum_tradingvalue = item['trading_value']

            if item['value'] > value:
                # print('買い')
                isBuy = True
            elif item['value'] < value:
                # print('売り')
                isBuy = False
            value = item['value']
        else:
            if sum_tradingvalue > 8000000:
                add_df = pd.DataFrame([[time, sum_tradingvalue, isBuy]],
                                      columns=["time", "trading_value", "isBuy"])
                result = pd.concat([result, add_df], axis=0)
            # 初期化
            time = item['time']
            sum_tradingvalue = item['trading_value']

        return result


def set_macro(sheet, codelist):
    for index, code in enumerate(codelist):
        sheet.cells(2, 1+index*3).value = ["時刻", "出来高", "約定値"]
        sheet.cells(
            1, 1+index*3).value = "=@RssTickList(,\"" + code+".T\",100)"


def enable_RSS():
    hwnd = win32gui.FindWindow(None, 'RSS_step_value_reader.xlsx - Excel')
    while not win32gui.IsWindowEnabled(hwnd):
        time.sleep(2)

    while sheet.cells(3, 1).value is None:
        print('RSS接続再試行')
        rect = win32gui.GetWindowRect(hwnd)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        pyautogui.click(rect[0]+1220, rect[1]+110)
        pyautogui.click(rect[0]+50, rect[1]+200)
        time.sleep(3)
    win32gui.ShowWindow(hwnd, 6)


if __name__ == '__main__':
    stocklist = pd.read_csv(
        'data/code_list.csv', header=0, encoding='cp932', dtype=str)
    codelist = stocklist['銘柄コード']

    wb = xw.Book()
    wb.app.api.RegisterXLL(
        r"C:/Users/kazuk/AppData/Local/MarketSpeed2/Bin/rss/MarketSpeed2_RSS_64bit.xll")
    wb.activate()
    sheet = wb.sheets.add()

    set_macro(sheet, codelist)
    wb.save('data/RSS_step_value_reader.xlsx')
    enable_RSS()

    bigTrade = BigTrade(stocklist, sheet)

    fin_pm = datetime.datetime.strptime("15:00:30", '%H:%M:%S').time()
    while datetime.datetime.now().time() < fin_pm:
        time.sleep(1)
        bigTrade.get_RSS_data(sheet)
        bigTrade.print_tradingvalue()

    wb.close()
