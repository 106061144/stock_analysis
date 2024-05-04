import shioaji as sj #將shioaji重新命名為sj
api = sj.Shioaji(simulation=True) #初始化時，simulation設為True，代表要使用模擬環境
api.login(
    person_id="PAPIUSER01", 
    passwd="2222"
)
api.logout() #登出