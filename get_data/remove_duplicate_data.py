import pandas as pd
from tqdm import tqdm


def main():
    fname = '6554_20211216_1130.csv'
    input_fname = 'data/'+fname
    row_df = pd.read_csv(input_fname,
                         header=0, index_col=0, encoding='cp932')
    unique_df = pd.DataFrame(columns=["時刻", "出来高", "約定値"])
    len_roe_df = len(row_df)
    # while n < (len_roe_df+1)/101-1:
    for n in tqdm(range(int((len_roe_df+1)/101))):
        # while n < 1000:
        # １秒ごとに入ってくるデータ
        in_data = row_df[101*n:101*(n+1)].reset_index(drop=True)

        unique_df = remove_duplicate(unique_df, in_data)
    out_fname = 'data/test/rd_'+fname
    unique_df.to_csv(out_fname, encoding='cp932')
    print('正常終了:'+str(n))

# 重複を覗いてoriginal_dfにinput_dfを結合してくれる関数

def remove_duplicate(original_df, input_df):
    input_df = input_df[input_df['時刻'] != '--------']
    # 何もデータが入っていない時は無視
    if len(input_df[0:1]['時刻'].values) != 0:
        # からであればとりあえずコピー
        if original_df.empty:
            original_df = input_df.dropna()
        else:
            i = 0
            while True:
                # input_dfの中で一致する行を探す
                while i < len(input_df) and not compare_df(original_df[:1], input_df[i:i+1]):
                    i += 1

                # 一致するのがなかったらすべて新しいデータなので全部追加
                if i == len(input_df):
                    print(input_df[:1])
                    original_df = pd.concat([input_df.dropna(), original_df])\
                            .reset_index(drop=True)
                    break
                else:
                    # それから先も比べてみる 最後まで比べるべき？10個くらいでいいかも
                    j = 1
                    while j+i < len(input_df) and j < len(original_df):
                        if not compare_df(original_df[j:j+1], input_df[i+j:i+j+1]):
                            i += 1
                            break
                        j += 1
                    # 一致(while文が正常終了)すればinput_dfのi番目のデータまでを連結する
                    else:
                        original_df = pd.concat(
                            [input_df[:i], original_df]).reset_index(drop=True)
                        break
    return original_df


def compare_df(df1, df2):
    for index in df1.columns:
        if df1[index].values != df2[index].values:
            return False
    return True


if __name__ == '__main__':
    main()
