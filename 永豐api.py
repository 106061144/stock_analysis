import shioaji as sj  # 將shioaji重新命名為sj
api = sj.Shioaji()
api.login(
    person_id="",
    passwd=""
)
api.logout()  # 登出
