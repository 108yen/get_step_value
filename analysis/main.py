from main_window import MainWindow
from big_trade import BigTrade
from rpa import RPA

if __name__ == '__main__':
    mainWindow=MainWindow()
    bigTrade=BigTrade(mainWindow)
    bigTrade.start()
    mainWindow.start_mainloop()

