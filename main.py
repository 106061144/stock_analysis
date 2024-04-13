from function import *

if __name__ == '__main__':

    stock_list = Update_potential_stock()
    [reward, time_stamp, Bollin_mask] = past_synthesis(stock_list[42], 2022, 1)
    print(reward)
    print(time_stamp)

    # for stock_no in stock_list:
    stock = Stock(stock_list[42])
    data = stock.fetch_from(2022,1)
    df = pd.DataFrame(data)
    
    time_tap = df['date'].tolist()
    volumn = df['capacity'].tolist()
    close_list = df['close'].tolist()
    [macd, diff, Hist] = MACD(close_list)
    
    ema7 = EMA_cal(7,close_list)
    Ma120 = MA_cal(120,close_list)
    bottom_line = EMA_cal(25, close_list)

    fig, axs = plt.subplots(3)
    axs[0].plot(time_tap,close_list, label='close')
    #axs[0].plot(time_tap,bottom_line, label='25 ave')
    axs[0].plot(time_tap,Bollin_mask[1], label='BL up', linestyle='dashed')
    axs[0].plot(time_tap,Bollin_mask[2], label='BL down', linestyle='dashed')
    #axs[0].legend()
    axs[1].bar(time_tap,Hist)
    axs[1].plot(time_tap,macd, label='macd')
    axs[1].plot(time_tap,diff, label='diff')
    axs[1].legend()
    axs[2].plot(time_tap,volumn, label='vol')
    axs[2].legend()
    plt.show()
