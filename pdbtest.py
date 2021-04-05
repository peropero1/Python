import pdb
# l(list): 列出所有的code
# n(next): 下一行
# c(continue): 繼續/離開debug
# p(print): 印出相關變數

first='First'
second="Second"
pdb.set_trace()
result=first+second
third="Third"
result+=third
print(result)