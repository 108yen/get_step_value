import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm

# 前日とかのチャートをプロットするやつ

# ５分足用のデータを作成


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
    five_min_data = pd.DataFrame(columns=["時刻", "始値", "終値", "高値", "低値", "出来高"])

    split5m = datetime.strptime("09:05:00", '%H:%M:%S')
    ini_time = datetime.strptime(
        row_df[:1]['時刻'].values[0], '%H:%M:%S').time()
    while ini_time >= split5m.time():
        split5m = split5m+timedelta(minutes=5)
    max = row_df[:1]['約定値'].values[0]
    min = row_df[:1]['約定値'].values[0]
    first = row_df[:1]['約定値'].values[0]
    fin = 0
    volume = 0
    for index, data in tqdm(row_df.iterrows()):
        value = int(data['約定値'])
        # 次の足に行くタイミング
        if split5m.time() <= datetime.strptime(data['時刻'], '%H:%M:%S').time():
            # 今はもう次の足の始値
            fin = row_df[index-2:index-1]['約定値'].values[0]
            five_min_data = five_min_data.append(
                pd.Series([split5m.strftime('%H:%M:%S'), first, fin, max, min, volume],
                          index=five_min_data.columns),
                ignore_index=True)
            # データ初期化
            max = value
            min = value
            first = value
            volume = 0
            while datetime.strptime(data['時刻'], '%H:%M:%S').time() >= split5m.time():
                split5m = split5m+timedelta(minutes=5)
        if value > max:
            max = value
        if value < min:
            min = value
        volume += int(data['出来高'])
    # 最後のデータを投入する
    fin = row_df[:-1]['約定値'].values[0]
    five_min_data = five_min_data.append(
        pd.Series([split5m.strftime('%H:%M:%S'), first, fin, max, min, volume],
                  index=five_min_data.columns),
        ignore_index=True)

    return five_min_data


def main():
    print(split_five_min_data('9212', '20211230'))


if __name__ == '__main__':
    main()
