import shioaji as sj  # 將shioaji重新命名為sj
api = sj.Shioaji()
api.login(
    person_id="G122339838",
    passwd="838933221gG"
)
api.logout()  # 登出
