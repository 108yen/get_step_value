import time
import _thread
import threading

import wx
import wx.lib.newevent

from big_trade import BigTrade

# 新しいイベントクラスとイベントを定義する
(MyThreadEvent, EVT_MY_THREAD) = wx.lib.newevent.NewEvent()

class MainWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(380, 400))

        panel = wx.Panel(self)
        self.text_disp = wx.TextCtrl(panel, style=wx.TE_MULTILINE)

        sizer = wx.BoxSizer()
        sizer.Add(self.text_disp, 1, wx.EXPAND)
        panel.SetSizer(sizer)

        # 新しく定義したイベントに対応する処理関数をバインドする
        self.Bind(EVT_MY_THREAD, self.OnUpdate)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        # スレッドのインスタンスを作り、起動する
        # self.my_thread = MyThread(self)
        # self.my_thread.start()
        self.my_thread=BigTrade(self,MyThreadEvent)
        self.my_thread.start()

        self.Centre()
        self.Show(True)

    def OnCloseWindow(self, evt):
        # スレッドが停止するまで待ってから、ウィンドウを閉じる
        self.my_thread.stop()

        while self.my_thread.isRunning():
            time.sleep(0.1)

        self.Destroy()

    def OnUpdate(self, evt):
        # スレッドからイベントを受信したときの処理
        self.text_disp.SetValue(evt.msg)


if __name__ == '__main__':
    app = wx.App()
    # デバッグするときはwx.PySimpleApp()を使う
    # app = wx.PySimpleApp()
    MainWindow(None, wx.ID_ANY, 'wxthr.py')
    app.MainLoop()
