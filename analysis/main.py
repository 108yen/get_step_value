from main_window import MainWindow
import wx
import wx.lib.newevent

if __name__ == '__main__':
    app = wx.App()
    # デバッグするときはwx.PySimpleApp()を使う
    # app = wx.PySimpleApp()
    MainWindow(None, wx.ID_ANY, 'bigtrade')
    app.MainLoop()

