from function import *

if __name__ == '__main__':

    stock_list = Update_potential_stock()
    # reward_list = []
    # for stock_id in stock_list[10:21]:
    #     [reward, time_stamp, Bollin_mask, consol_date] = past_synthesis(stock_id, 2022, 1)
    #     reward_list.append(sum(reward))
    #     #print(time_stamp)
    # print(reward_list)

    # plot and analysis
    [reward, time_stamp, Bollin_mask, consol_date] = past_synthesis(
        stock_list[18], 2022, 1, print_log=True)
    print(reward)
    print(time_stamp)
    stock = Stock(stock_list[18])
    data = stock.fetch_from(2022, 1)
    df = pd.DataFrame(data)

    time_tap = df['date'].tolist()
    volumn = df['capacity'].tolist()
    close_list = df['close'].tolist()
    [macd, diff, Hist] = MACD(close_list)

    # ema7 = EMA_cal(7,close_list)
    # bottom_line = EMA_cal(25, close_list)

    fig, axs = plt.subplots(3)
    axs[0].plot(time_tap, close_list, label='close')
    # axs[0].plot(time_tap,bottom_line, label='25 ave')
    axs[0].plot(time_tap, Bollin_mask[1], label='BL up', linestyle='dashed')
    axs[0].plot(time_tap, Bollin_mask[2], label='BL down', linestyle='dashed')
    for date_set in consol_date:
        axs[0].axvspan(date_set[0], date_set[1], facecolor='pink', alpha=0.2)
    # axs[0].legend()
    axs[1].bar(time_tap, Hist)
    axs[1].plot(time_tap, macd, label='macd')
    axs[1].plot(time_tap, diff, label='diff')
    axs[1].legend()
    axs[2].plot(time_tap, volumn, label='vol')
    axs[2].legend()
    plt.show()
