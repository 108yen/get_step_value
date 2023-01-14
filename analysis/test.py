import time
import _thread
import threading

import wx
import wx.lib.newevent

# 新しいイベントクラスとイベントを定義する
(MyThreadEvent, EVT_MY_THREAD) = wx.lib.newevent.NewEvent()


class MyThread(threading.Thread):
    def __init__(self, win):
        super(MyThread,self).__init__()
        self.win = win

    def Stop(self):
        self.keepGoing = False

    def IsRunning(self):
        return self.running

    def run(self):
        self.keepGoing = True
        self.running = True
        while self.keepGoing:
            ts = time.strftime('%Y/%d/%m %H:%M:%S', time.localtime())
            # メッセージを格納したイベントを作る
            evt = MyThreadEvent(msg=ts)
            # イベントを投げる
            wx.PostEvent(self.win, evt)
            time.sleep(1)

        self.running = False


class MainWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(380, 200))

        panel = wx.Panel(self)
        self.text_disp = wx.TextCtrl(panel, style=wx.TE_MULTILINE)

        sizer = wx.BoxSizer()
        sizer.Add(self.text_disp, 1, wx.EXPAND)
        panel.SetSizer(sizer)

        # 新しく定義したイベントに対応する処理関数をバインドする
        self.Bind(EVT_MY_THREAD, self.OnUpdate)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        # スレッドのインスタンスを作り、起動する
        self.my_thread = MyThread(self)
        self.my_thread.start()

        self.Centre()
        self.Show(True)

    def OnCloseWindow(self, evt):
        # スレッドが停止するまで待ってから、ウィンドウを閉じる
        self.my_thread.Stop()

        while self.my_thread.IsRunning():
            time.sleep(0.1)

        self.Destroy()

    def OnUpdate(self, evt):
        # スレッドからイベントを受信したときの処理
        self.text_disp.AppendText(evt.msg+'\n')


app = wx.App()
# デバッグするときはwx.PySimpleApp()を使う
#app = wx.PySimpleApp()
MainWindow(None, wx.ID_ANY, 'wxthr.py')
app.MainLoop()
