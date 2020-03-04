def make_icecream(*toppings):
    #列出配方
    print("Formula of this Icecream: ")
    for element in toppings:
        print('---',element)
def make_drink(size,drink):
    print("所點飲料如下： ")
    print('---',size.title())
    print('---',drink.title())