from banks1 import Banks
	# 注意這邊也要import
class Shilin_Banks(Banks):
    def __init__(self,uname):
        self.__title="Taipei Bank-Shilin Branch"
    def bank_title(self):
        return self.__title