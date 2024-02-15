from Crypto.Util import number

heavy=0
light=0
size=0
exponential_decay=0
seed=[]
topk=0

def Set_default(h,l,s,decay,t):
    global heavy
    global light
    global size
    global seed
    global exponential_decay
    global topk
    heavy=h
    light=l
    size=s
    exponential_decay=decay
    seed=[number.getPrime(32) for i in range(2)]
    topk=t
    # return heavy,light,size,seed,exponential_decay