import re
import subprocess
import time
from pathlib import Path

import xlwings as xw


def get_xl_path() -> Path:
    #Excelのインストール先パスを返す関数
    subprocess_rtn = (
        subprocess
        .run(['assoc', '.xlsx'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        .stdout.decode("utf8")
    )
    assoc_to = re.search('Excel.Sheet.[0-9]+', subprocess_rtn).group()

    subprocess_rtn = (
        subprocess
        .run(['ftype', assoc_to], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        .stdout.decode('utf-8')
    )
    xl_path = re.search('C:.*EXCEL.EXE', subprocess_rtn).group()

    return Path(xl_path)


def xw_apps_add_fixed() -> xw.App:
    #Excelインスタンスを生成する関数
    xl_path = get_xl_path()
    num = xw.apps.count
    pid = subprocess.Popen([str(xl_path), '/e']).pid

    #xlwingsから認識できるまで待つ
    while xw.apps.count == num:
        time.sleep(1)

    #xlwingsから使用できるようになるまで待つ
    while True:
        try:
            xw.apps[pid].activate()
            break
        except:
            time.sleep(1)

    return xw.apps[pid]
