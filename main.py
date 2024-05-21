from function import *

if __name__ == '__main__':

    stock_list = Update_potential_stock()
    # reward_list = []
    # qualified_stock = []
    # for stock_id in stock_list[11:21]:
    #     flag = qualify_stock(stock_id, 2023, 1)
    #     if flag:
    #         qualified_stock.append(stock_id)
    #         [reward, time_stamp, Bollin_mask,
    #             consol_date] = past_synthesis(stock_id, 2023, 1, plotting=False)
    #         reward_list.append(sum(reward))
    #     # print(time_stamp)
    # print(qualified_stock)
    # print(reward_list)

    # plot and analysis
    figure_plot(stock_list[11], 2023, 1)
