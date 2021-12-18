import pandas as pd


def main():
    row_df = pd.read_csv('data/6554_20211215_1130.csv',
                         header=0, index_col=0, encoding='cp932')
    unique_df = pd.DataFrame(columns=["時刻", "出来高", "約定値"])
    len_roe_df = len(row_df)
    n = 0
    while 101*(n+1) <= len_roe_df:
    # while n < 1000:
        # １秒ごとに入ってくるデータ
        in_data = row_df[101*n:101*(n+1)].reset_index(drop=True)
        in_data = in_data[in_data['時刻'] != '--------']
        # 何もデータが入っていない時は無視
        if in_data[0:1]['時刻'].values != '--------':
            # からであればとりあえずコピー
            if unique_df.empty:
                unique_df = in_data.dropna()
            else:
                i = 0
                flag = True
                while flag:
                    # in_dataの中で一致する行を探す
                    while not compare_df(unique_df[:1], in_data[i:i+1]) and i < len(in_data):
                        i += 1

                    # 一致するのがなかったらすべて新しいデータなので全部追加
                    if i == len(in_data)+1:
                        unique_df = pd.concat(
                            [in_data.dropna(), unique_df]).reset_index(drop=True)
                        unique_df = unique_df[unique_df['時刻'] != '--------']
                        flag = False
                    else:
                        # それから先も比べてみる 最後まで比べるべき？10個くらいでいいかも
                        j = 1
                        while j+i < len(in_data) and j < len(unique_df):
                            if not compare_df(unique_df[j:j+1], in_data[i+j:i+j+1]):
                                i += 1
                                break
                            j += 1
                        # 一致(while文が正常終了)すればin_dataのi番目のデータまでを連結する
                        else:
                            unique_df = pd.concat(
                                [in_data[:i], unique_df]).reset_index(drop=True)
                            flag = False
        n += 1
        if n%1000==0:
            print(n)
    fname='data/test/remove_duplicate.csv'
    unique_df.to_csv(fname, encoding='cp932')
    print('正常終了')


def compare_df(df1, df2):
    for index in df1.columns:
        if df1[index].values != df2[index].values:
            return False
    return True


if __name__ == '__main__':
    main()
