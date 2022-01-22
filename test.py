import pandas as pd


def main():
    fname = 'data/code_list.csv'
    codename_list = pd.read_csv(fname, header=0,encoding='utf8')
    try:
        print(codename_list[codename_list['コード']==73]['銘柄名'].values[0])
    except IndexError:
        print('エラー') 

if __name__ == '__main__':
    main()
