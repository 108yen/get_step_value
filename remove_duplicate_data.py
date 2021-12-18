import pandas as pd

# todo:データフレーム二つ入れたら、いい感じに結合して返してくれるようにする
def main():
    input_fname = 'data/6554_20211215_1130.csv'
    row_df = pd.read_csv(input_fname,
                         header=0, index_col=0, encoding='cp932')
    unique_df = pd.DataFrame(columns=["時刻", "出来高", "約定値"])
    len_roe_df = len(row_df)
    n = 0
    while 101*(n+1) <= len_roe_df:
    # while n < 1000:
        # １秒ごとに入ってくるデータ
        in_data = row_df[101*n:101*(n+1)].reset_index(drop=True)

        unique_df=remove_duplicate(unique_df,in_data)
        n += 1
        if n%1000==0:
            print(n)
    out_fname='data/test/remove_duplicate.csv'
    unique_df.to_csv(out_fname, encoding='cp932')
    print('正常終了')

# 重複を覗いてoriginal_dfにinput_dfを結合してくれる関数
def remove_duplicate(original_df,input_df):
    input_df = input_df[input_df['時刻'] != '--------']
    # 何もデータが入っていない時は無視
    if input_df[0:1]['時刻'].values != '--------':
        # からであればとりあえずコピー
        if original_df.empty:
            original_df = input_df.dropna()
        else:
            i = 0
            flag = True
            while flag:
                # input_dfの中で一致する行を探す
                while not compare_df(original_df[:1], input_df[i:i+1]) and i < len(input_df):
                    i += 1

                # 一致するのがなかったらすべて新しいデータなので全部追加
                if i == len(input_df)+1:
                    original_df = pd.concat(
                        [input_df.dropna(), original_df]).reset_index(drop=True)
                    original_df = original_df[original_df['時刻']
                                                       != '--------']
                    flag = False
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
                        flag = False
    return original_df

def compare_df(df1, df2):
    for index in df1.columns:
        if df1[index].values != df2[index].values:
            return False
    return True


if __name__ == '__main__':
    main()
