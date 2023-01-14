
import datetime
import os
import threading
import time
import xlwings as xw
import pandas as pd
from rpa import RPA
import pythoncom
import wx
import wx.lib.newevent


class BigTrade(threading.Thread):
    def __init__(self, mainWindow, myThreadEvent) -> None:
        super(BigTrade, self).__init__()
        self.bigTradeList = {}
        self.mainWindow = mainWindow
        self.myTheadEvent = myThreadEvent

    # def get_sheet(self):
    #     xw.apps()
    def stop(self):
        self.keepGoing = False

    def isRunning(self):
        return self.running

    def run(self) -> None:
        self.keepGoing = True
        self.running = True

        # excel起動
        self.start_excel()

        fin_pm = datetime.datetime.strptime("15:00:30", '%H:%M:%S').time()
        while datetime.datetime.now().time() < fin_pm and self.keepGoing:
        # while self.keepGoing:
            time.sleep(1)
            self.get_RSS_data()
            # self.update_tree()
            self.print_tradingvalue()
            # self.test_print()

        self.rpa.close_wb()
        self.running = False

    def start_excel(self):
        pythoncom.CoInitialize()
        self.rpa = RPA()
        self.stocklist = self.rpa.get_stocklist()
        self.codelist = self.stocklist['銘柄コード']
        self.wb = xw.Book('RSS_step_value_reader.xlsx')
        self.sheet = self.wb.sheets['RSS']
        # データフレーム用意
        for code in self.codelist:
            self.bigTradeList[code] = pd.DataFrame(
                columns=["time", "trading_value", "isBuy"])

    def get_RSS_data(self):
        for index, code in enumerate(self.codelist):
            try:
                RSS_data = pd.DataFrame(self.sheet.range(
                    (3, 1+index*3), (103, 3+index*3)).value, columns=["time", "volume", "value"])
            except Exception as e:
                print(f'get RSS data Error: {e}')
                return

            # 計算のため、余計なデータ削除
            RSS_data = RSS_data[RSS_data['time'] != '--------'].dropna()
            RSS_data['trading_value'] = RSS_data['volume']*RSS_data['value']
            # print(RSS_data)
            big_trade = self.filter_big_trade(RSS_data)
            # print(big_trade)
            self.bigTradeList[code] = pd.concat(
                [self.bigTradeList[code], big_trade]).drop_duplicates(subset='time')

    def update_tree(self):
        for index, code in enumerate(self.codelist):
            # 5分間抽出
            fivemin_delay = datetime.datetime.now()-datetime.timedelta(minutes=5)
            recent_trade = self.bigTradeList[code][self.bigTradeList[code]
                                                   ['time'] > fivemin_delay.strftime('%H:%M:%S')]
            recent_trade = recent_trade[recent_trade['isBuy']].reset_index(
                drop=True)
            symbol_info = self.stocklist[self.stocklist['銘柄コード']
                                         == code].iloc[0]
            tree_val = self.mainWindow.get_tree(symbol_info['銘柄名'])

            if len(recent_trade) != 0:
                print('update')
                self.mainWindow.update_tree(code, symbol_info['銘柄名'], len(
                    recent_trade), recent_trade['trading_value'].sum())
            elif tree_val != None:
                self.mainWindow.delete_tree(symbol_info['銘柄名'])

    def test_print(self):
        display_message = ''
        for index, code in enumerate(self.codelist):
            if len(self.bigTradeList[code]) != 0:
                symbol_info = self.stocklist[self.stocklist['銘柄コード']
                                             == code].iloc[0]
                # 銘柄情報
                # print('\n'+symbol_info['銘柄コード']+' '+symbol_info['銘柄名'])
                display_message += symbol_info['銘柄コード'] + \
                    ' '+symbol_info['銘柄名']+'\n'
                # 大人買い情報
                # print(recent_trade)
                for index, item in self.bigTradeList[code].iterrows():
                    # print(index+' '+item['time']+' '+item['trading_value'])
                    i_time = item['time']
                    i_trading_value = ("{:,.2f}".format(
                        item['trading_value']))[:-8]
                    display_message += f'{index} {i_time} {i_trading_value}万\n'

        evt = self.myTheadEvent(msg=display_message)
        wx.PostEvent(self.mainWindow, evt)
        # print(display_message)

    def print_tradingvalue(self):
        display_message = ''
        # os.system('cls')
        for index, code in enumerate(self.codelist):
            # 5分間抽出
            fivemin_delay = datetime.datetime.now()-datetime.timedelta(minutes=5)
            recent_trade = self.bigTradeList[code][self.bigTradeList[code]
                                                   ['time'] > fivemin_delay.strftime('%H:%M:%S')]
            recent_trade = recent_trade[recent_trade['isBuy']].reset_index(
                drop=True)

            if len(recent_trade) != 0:
                symbol_info = self.stocklist[self.stocklist['銘柄コード']
                                             == code].iloc[0]
                # 銘柄情報
                # print('\n'+symbol_info['銘柄コード']+' '+symbol_info['銘柄名'])
                display_message += symbol_info['銘柄コード'] + \
                    ' '+symbol_info['銘柄名']+'\n'
                # 大人買い情報
                # print(recent_trade)
                for index, item in recent_trade.iterrows():
                    # print(index+' '+item['time']+' '+item['trading_value'])
                    i_time = item['time']
                    i_trading_value = ("{:,.2f}".format(
                        item['trading_value']))[:-8]
                    display_message += f'{index} {i_time} {i_trading_value}万\n'

        evt = self.myTheadEvent(msg=display_message)
        wx.PostEvent(self.mainWindow, evt)
        # print(display_message)

    # RSS_data=pd.DataFrame(columns = ["time", "volume", "value", "trading_value"])

    def filter_big_trade(self, RSS_data) -> pd.DataFrame:
        reverse_RSS_data = RSS_data.iloc[::-1].reset_index(drop=True)
        result = pd.DataFrame()

        if len(reverse_RSS_data) == 0:
            return result

        time = reverse_RSS_data.loc[0, 'time']
        value = reverse_RSS_data.loc[0, 'value']
        isBuy = True
        sum_tradingvalue = 0
        for index, item in reverse_RSS_data.iterrows():

            if item['value'] > value and isBuy and time == item['time']:
                # print('買い')
                sum_tradingvalue += item['trading_value']
            elif item['value'] < value and not isBuy and time == item['time']:
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
