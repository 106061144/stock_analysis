from function import *

if __name__ == '__main__':
    #Create_stock_index_table()
    # df = pd.read_csv('stock_index.csv')
    # stock_no = df['stock_code'][0]
    stock_list = Update_potential_stock()
    [reward, time_stamp] = past_synthesis('2884')
    print(reward)
    print(time_stamp)
    # for stock_no in stock_list:
    # stock = Stock('0050')
    # data = stock.fetch_from(2024,1)
    # df = pd.DataFrame(data)
    # time_tap = df['date'].tolist()
    # close_list = df['close'].tolist()
    # [macd, diff, Hist] = MACD(close_list)
    
    # ema7 = EMA_cal(7,close_list)

    # fig, axs = plt.subplots(2)
    # axs[0].plot(time_tap,ema7, label='ema_7')
    # axs[1].bar(time_tap,Hist)
    # axs[1].plot(time_tap,macd, label='macd')
    # axs[1].plot(time_tap,diff, label='diff')
    # axs[1].legend()
    # plt.show()
