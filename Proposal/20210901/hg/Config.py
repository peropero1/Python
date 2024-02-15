from Crypto.Util import number

heavy=0
light=0
size=0
exponential_decay=0
seed=[]

def Set_default(h,l,s,decay):
    global heavy
    global light
    global size
    global seed
    global exponential_decay
    heavy=h
    light=l
    size=s
    exponential_decay=decay
    seed=[number.getPrime(32) for i in range(2)]
    # return heavy,light,size,seed,exponential_decay