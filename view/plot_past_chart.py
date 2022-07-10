import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import tkinter
import os
from sqlalchemy import create_engine
import db_conf
import mysql.connector

# 前日とかのチャートをプロットするやつ

# todo:出来高０でもレコードとしては格納すべき
# todo:５分ずれているのでどこかで修正すべき
def split_five_min_data(code: str, date: str):
    # 午前午後分かれてないパターン
    fname='data/'+date+'/'+code+'.csv'
    row_df = pd.read_csv(fname, header=0, index_col=0,
                         encoding='cp932').iloc[::-1].reset_index(drop=True)
    # engine = create_engine(
    #     'mysql+mysqlconnector://'+db_conf.db_user+':'+db_conf.db_pass+'@'+db_conf.db_ip+'/stock')
    # row_df = pd.read_sql_query('SELECT concat(cast(date as char),\' \',cast(time as char)) AS datetime,value,volume FROM step WHERE (`date` IN (\'2022-04-15\')) AND (code='+code+') ORDER BY dayindex ASC', \
    #     con=engine, parse_dates={'datetime':'%Y-%m-%d %H:%M:%S'})
    # 出力予定のデータ
    five_min_data = pd.DataFrame(
        columns=["時刻", "始値", "終値", "高値", "低値", "買い出来高", "売り出来高", "出来高", "VWAP"])

    split5m = datetime.strptime("09:05:00", '%H:%M:%S')
    ini_time = datetime.strptime(
        row_df[:1]['時刻'].values[0], '%H:%M:%S').time()
    while ini_time >= split5m.time():
        split5m = split5m+timedelta(minutes=5)
    max = row_df[:1]['約定値'].values[0]
    min = row_df[:1]['約定値'].values[0]
    first = row_df[:1]['約定値'].values[0]
    fin = 0
    buy_dir = True
    buy_vol = 0
    sell_vol = 0
    volume = 0
    pre_value = 0
    # VWAP用
    sum_volume = 0
    trading_price = 0
    for index, data in tqdm(row_df.iterrows(),total=len(row_df)):
        value = int(data['約定値'])
        # 次の足に行くタイミング
        if split5m.time() <= datetime.strptime(data['時刻'], '%H:%M:%S').time():
            # ひとつ前の値が終値
            fin = row_df[index-1:index]['約定値'].values[0]
            vwap = trading_price/sum_volume
            five_min_data = pd.concat([five_min_data,pd.DataFrame([[split5m.strftime('%H:%M:%S'), first, fin, max, min, buy_vol, sell_vol, volume, vwap]],
                        columns=five_min_data.columns)],ignore_index=True)
            # データ初期化
            max = value
            min = value
            first = value
            volume = 0
            buy_vol = 0
            sell_vol = 0
            while datetime.strptime(data['時刻'], '%H:%M:%S').time() >= split5m.time():
                split5m = split5m+timedelta(minutes=5)
        if value > max:
            max = value
        if value < min:
            min = value
        # 出来高の処理
        if value > pre_value:
            buy_dir = True
        elif value < pre_value:
            buy_dir = False
        pre_value = value
        if buy_dir:
            buy_vol += int(data['出来高'])
        else:
            sell_vol += int(data['出来高'])
        volume += int(data['出来高'])
        # VWAPの処理
        sum_volume += int(data['出来高'])
        trading_price += value*int(data['出来高'])
    # 最後のデータを投入する
    fin = row_df[-1:]['約定値'].values[0]
    vwap = trading_price/sum_volume
    five_min_data = pd.concat([five_min_data,pd.DataFrame([[split5m.strftime('%H:%M:%S'), first, fin, max, min, buy_vol, sell_vol, volume, vwap]],
                columns=five_min_data.columns)],ignore_index=True)

    return five_min_data


# canvasにプロットする 800x450(300)
"""
canvasにチャートを描画
入力
canvas: tkinter.Canvas
code:   string
date:   string
出力
candle_rate:    ローソク足の縮小率
volume_rate:    出来高の縮小率
max_val:    その日の高値
min_val:    その日の低値
five_min_data.index-1:  データ数(0からのカウントなので-1)
"""


def plot(canvas:tkinter.Canvas, code:str, date:datetime.date):
    if not data_isexist(code,date):
        return 1,1,0,999999,0

    candle_width = 4
    five_min_data = split_five_min_data(code, date.strftime('%Y%m%d'))
    # 高値と低値から倍率を決める
    max_val = five_min_data['高値'].max()
    min_val = five_min_data['低値'].min()
    candle_rate = 300/(max_val-min_val)
    # 最初の足の始値と位置（これを基準に描画する）
    ini_val = five_min_data[:1]['始値'].values[0]
    defy = 300-int((ini_val-min_val)*candle_rate)
    # 出来高の倍率を決める
    max_volume = five_min_data['出来高'].max()
    volume_rate = 150/max_volume
    # VWAPの描画用
    pre_vwap_fy = defy
    pre_vwap_fx = 10+candle_width//2
    for index, data in five_min_data.iterrows():
        # vwapの計算
        vwap_sy = pre_vwap_fy
        vwap_fy = defy-(data['VWAP']-ini_val)*candle_rate
        pre_vwap_fy = vwap_fy
        vwap_sx = pre_vwap_fx
        vwap_fx = 10+(candle_width+3)*index+candle_width//2
        pre_vwap_fx = vwap_fx
        # ローソク足の計算
        candle_sy = defy-(data['始値']-ini_val)*candle_rate
        candle_fy = candle_sy-(data['終値']-data['始値'])*candle_rate
        candle_sx = 10+(candle_width+3)*index
        candle_fx = candle_sx+candle_width
        color = 'red' if data['終値'] >= data['始値'] else 'blue'
        # ひげの計算
        line_x = candle_sx+candle_width//2
        line_sy = defy-(data['低値']-ini_val)*candle_rate
        line_fy = defy-(data['高値']-ini_val)*candle_rate
        # 出来高の計算
        volume_fy = 450-data['出来高']*volume_rate
        sell_vol_fy = 450-data['売り出来高']*volume_rate
        # VWAP配置
        canvas.create_line(vwap_sx, vwap_sy, vwap_fx, vwap_fy,
                           fill='#ff6347', tag='vwap'+str(index))
        canvas.lower('vwap'+str(index))
        # ヒゲ配置
        canvas.create_line(line_x, line_sy, line_x,
                           line_fy, tag='line'+str(index))
        # ローソク足配置
        canvas.create_rectangle(candle_sx, candle_sy,
                                candle_fx, candle_fy, fill=color, tag='rect'+str(index))
        # 出来高配置
        buy_col = '#cd5c5c'
        sell_col = '#4169e1'
        canvas.create_line(line_x, 450, line_x,
                           sell_vol_fy, width=5, fill=sell_col, tag='sell_volume'+str(index))
        canvas.create_line(line_x, sell_vol_fy, line_x,
                           volume_fy, width=5, fill=buy_col, tag='buy_volume'+str(index))

    return candle_rate, volume_rate, max_val, min_val, len(five_min_data.index)-1

# todo:dateをstringにしたりいろいろしている所整理したい
def data_isexist(code:str,date:datetime.date):
    db_config={
        'user':db_conf.db_user,
        'password':db_conf.db_pass,
        'host':db_conf.db_ip,
        'database':'stock'
    }
    try:
        cnx=mysql.connector.connect(**db_config)
        cur=cnx.cursor(buffered=True)
        cur.execute('select exists(select * from getdate where  (`date` IN (\''+date.strftime('%Y-%m-%d')+'\')) AND (code='+code+'));')
        cnx.commit()
        if cur.fetchone()[0]==0:
            cur.close()
            cnx.close()
            return False
        else:
            cur.close()
            cnx.close()
            return True
    except Exception as e:
        print(e)
        return False

        
def main():
    # root = tkinter.Tk()
    # root.title(u"GEI")
    # root.geometry("800x450")  # ウインドウサイズ（「幅x高さ」で指定）

    # # キャンバスエリア
    # canvas = tkinter.Canvas(root, width=800, height=450)
    # plot(canvas, '6524', '20220107')

    # canvas.place(x=0, y=0)
    # root.mainloop()
    code_list = ['9519', '9258', '9257', '9254', '9212', '9211', '9107',
                 '7133', '7383', '7254',
                 '6554', '6524', '6522',
                 '5759',
                 '4599', '4591', '4418', '4417', '4414', '4412', '4260', '4261', '4263', '4264', '4265', '4259', '4125', '4080',
                 '2585', '2484', '2427', '2158']
    new_dir_path = 'data/20220114/5min'
    for code in code_list:
        # print(code)
        os.makedirs(new_dir_path, exist_ok=True)
        fname = new_dir_path+'/'+code+'.csv'
        split_five_min_data(code, '20220114').to_csv(fname, encoding='cp932')


if __name__ == '__main__':
    main()
