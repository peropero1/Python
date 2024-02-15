import sys
sys.path.append("..")
import numpy as np
from Tools import Func
from Tools import Config

class CountMinSketch():
    def __init__(self,width=None,depth=None):
        """ default initilization function """
        # default values
        self.__width = 0
        self.__depth = 0
        self.__sketch=[]
        if width is not None and depth is not None:
            self.__width = int(width)
            self.__depth = int(depth)
            self.__sketch=np.zeros((self.__depth,self.__width),dtype='int32')
    def __str__(self):
        """ string representation of the count min sketch """
        msg = (
            "Count-Min Sketch:\n"
            "\tWidth: {0}\n"
            "\tDepth: {1}\n"
            "\tSketch: \n{2}\n"
        )
        return msg.format(
            self.__width,
            self.__depth,
            self.__sketch
        )            
    def Add_CMS(self,element):
        # insert element=<ID,count>
        #index_li=[0 for _ in range(self.__depth)]
        for row in range(self.__depth):
            col=Func.position(element,row)
            #index_li[row]=col
            self.__sketch[row][col]+=element.count
        return 0
    
    def Estimate_CMS(self,element):
        countlist=[]
        for row in range(self.__depth):
            col=Func.position(element,row)
            countlist.append(self.__sketch[row][col])    
        return min(countlist)
    
    @property
    def width(self):
        """int: The width of the count-min sketch

        Note:
            Not settable"""
        return self.__width    
    @property
    def depth(self):
        """int: The depth of the count-min sketch

        Note:
            Not settable"""
        return self.__depth

    @property
    def sketch(self):
        """whole sketch array of the count-min sketch

        Note:
            Not settable"""
        return self.__sketch
