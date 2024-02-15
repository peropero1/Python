from Node import DS
from Crypto.Util import number

e_max=DS.Tail("",0)
width=0
depth=0
size=0
topk=0
seed=[]

def Set_default(w,d,s,t):
    global width
    global depth
    global size
    global seed
    global topk
    width=w
    depth=d
    size=s
    topk=t
    seed=[number.getPrime(32) for i in range(2)]
    #return width,depth,size,seed,topk


