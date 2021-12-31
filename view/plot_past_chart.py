import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import tkinter

# 前日とかのチャートをプロットするやつ


def split_five_min_data(code, date):
    # 午前ぶん
    fname = code+'_'+date+'_1130.csv'
    input_fname = 'data/'+fname
    am_data = pd.read_csv(input_fname, header=0, index_col=0,
                          encoding='cp932').iloc[::-1]
    # 午後ぶん
    fname = code+'_'+date+'_1500.csv'
    input_fname = 'data/'+fname
    pm_data = pd.read_csv(input_fname, header=0, index_col=0,
                          encoding='cp932').iloc[::-1]
    pm_data = pm_data[pm_data['時刻'] > "11:30:00"]
    row_df = pd.concat([am_data, pm_data]).reset_index(drop=True)
    # 出力予定のデータ
    five_min_data = pd.DataFrame(
        columns=["時刻", "始値", "終値", "高値", "低値", "買い出来高", "売り出来高", "出来高"])

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
    for index, data in tqdm(row_df.iterrows()):
        value = int(data['約定値'])
        # 次の足に行くタイミング (9時ちょうどから始まるやつはエラーになるかも?9:05にしてるから大丈夫か？)
        if split5m.time() <= datetime.strptime(data['時刻'], '%H:%M:%S').time():
            # 今はもう次の足の始値
            fin = row_df[index-2:index-1]['約定値'].values[0]
            five_min_data = five_min_data.append(
                pd.Series([split5m.strftime('%H:%M:%S'), first, fin, max, min, buy_vol, sell_vol, volume],
                          index=five_min_data.columns),
                ignore_index=True)
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
    # 最後のデータを投入する
    fin = row_df[-1:]['約定値'].values[0]
    five_min_data = five_min_data.append(
        pd.Series([split5m.strftime('%H:%M:%S'), first, fin, max, min, buy_vol, sell_vol, volume],
                  index=five_min_data.columns),
        ignore_index=True)

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

def plot(canvas, code, date):
    candle_width = 4
    five_min_data = split_five_min_data(code, date)
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
    for index, data in five_min_data.iterrows():
        # ローソク足の計算
        candle_sy = defy-int((data['始値']-ini_val)*candle_rate)
        candle_fy = candle_sy-int((data['終値']-data['始値'])*candle_rate)
        candle_sx = 10+(candle_width+3)*index
        candle_fx = candle_sx+candle_width
        color = 'red' if data['終値'] >= data['始値'] else 'blue'
        # ひげの計算
        line_x = candle_sx+candle_width//2
        line_sy = defy-int((data['低値']-ini_val)*candle_rate)
        line_fy = defy-int((data['高値']-ini_val)*candle_rate)
        # 出来高の計算
        volume_fy = 450-int(data['出来高']*volume_rate)
        sell_vol_fy = 450-int(data['売り出来高']*volume_rate)
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
                           sell_vol_fy, width=5, fill=sell_col, tag='buy_volume'+str(index))
        canvas.create_line(line_x, sell_vol_fy, line_x,
                           volume_fy, width=5, fill=buy_col, tag='sell_volume'+str(index))

    return candle_rate, volume_rate, max_val, min_val, five_min_data.index-1


def main():
    root = tkinter.Tk()
    root.title(u"GEI")
    root.geometry("800x450")  # ウインドウサイズ（「幅x高さ」で指定）

    # キャンバスエリア
    canvas = tkinter.Canvas(root, width=800, height=450)
    print(plot(canvas, '9212', '20211229'))

    canvas.place(x=0, y=0)
    root.mainloop()


if __name__ == '__main__':
    main()
