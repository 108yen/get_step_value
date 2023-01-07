import threading
import time
import tkinter as tk
from tkinter import ttk


class MainWindow():
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title('test')
        self.root.geometry('400x300')
        self.create_tree()

    def start_mainloop(self):
        self.root.mainloop()

    def create_tree(self):
        column = ('code', 'name', 'num', 'value')
        self.tree = ttk.Treeview(self.root, columns=column)

        self.tree.column('#0', width=0, stretch='no')
        self.tree.column('code', anchor='center', width=80)
        self.tree.column('name', anchor='center', width=80)
        self.tree.column('num', anchor='e', width=80)
        self.tree.column('value', anchor='e', width=80)

        self.tree.heading('code', anchor='center', text='code')
        self.tree.heading('name', anchor='center', text='name')
        self.tree.heading('num', anchor='center', text='num')
        self.tree.heading('value', anchor='center', text='value')

        self.tree.pack()

    def delete_tree(self, name: str):
        self.tree.delete(name)
        self.tree.update()

    def update_tree(self, code: int, name: str, num: int, value: int):
        if self.tree.exists(name):
            self.tree.item(name, values=(code, name, num, ("{:,.2f}万".format(
                value))[:-8],))
        else:
            self.tree.insert(parent='', iid=name, index='end',
                             values=(code, name, num,  ("{:,.2f}万".format(
                                 value))[:-8],))
        self.root.update()

    def get_tree(self, name: str):
        if self.tree.exists(name):
            return self.tree.item(name)
        else:
            return None


if __name__ == '__main__':
    mainWindow = MainWindow()
    # mainWindow.insert_tree(code=9999,name='テスト',num=2,value=500)
