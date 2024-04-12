from function import *

if __name__ == '__main__':
    #Create_stock_index_table()
    # df = pd.read_csv('stock_index.csv')
    # stock_no = df['stock_code'][0]

    stock_list = Update_potential_stock()
    [reward, time_stamp] = past_synthesis(stock_list[10])
    print(reward)
    print(time_stamp)

    # for stock_no in stock_list:
    stock = Stock(stock_list[10])
    data = stock.fetch_from(2023,1)
    df = pd.DataFrame(data)
    
    time_tap = df['date'].tolist()
    volumn = df['capacity'].tolist()
    close_list = df['close'].tolist()
    [macd, diff, Hist] = MACD(close_list)
    
    ema7 = EMA_cal(7,close_list)
    bottom_line = EMA_cal(30, close_list)

    fig, axs = plt.subplots(3)
    axs[0].plot(time_tap,close_list, label='close')
    axs[0].plot(time_tap,bottom_line, label='30 ave')
    axs[1].bar(time_tap,Hist)
    axs[1].plot(time_tap,macd, label='macd')
    axs[1].plot(time_tap,diff, label='diff')
    axs[1].legend()
    axs[2].plot(time_tap,volumn, label='vol')
    plt.show()
