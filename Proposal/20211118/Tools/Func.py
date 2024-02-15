from Node import DS
from Tools import Config
import pandas as pd
import os
import spookyhash
import mmh3
import sys

import matplotlib.pyplot as plt
import numpy as np
import math

import tracemalloc
import linecache

# ==========================Tools=========================  

# ==========================UpdateSk==========================
def UpdateSk(element,Sk_head,Sk):
    #e_max=Config.e_max
    col,row=positionCS(element)
        # col / row index of element
    # ==========================update sketch==========================
    Sk_head[row].count+=element.count
    Sk_head[row].distinct.add(element.ID)
    #Sk[row][col]+=1
    Sk[row][col]+=element.count
    Update_local_max(Sk_head[row],Sk[row],element,col)

# ==========================update local max==========================       
def Update_local_max(head_item,element_list,element,column):
    # head_item: Sk_head[row]
    # element_list: Sketch[row]
    width,depth=Config.width,Config.depth
    local_max_col,local_max_row=positionCS(DS.Tail(head_item.maxID,0))
    lhh_index=0
    if head_item.maxID=='':
        head_item.maxID=element.ID
        head_item.keep=element.count
        lhh_index=column
    elif head_item.maxID==element.ID:
        head_item.keep+=element.count
        lhh_index=column
    else:
        # head_item.maxID != element.ID:
        if local_max_col==column:
            # lhh collision with e          
            head_item.keep-=element.count
            if head_item.keep<0:
                head_item.maxID=element.ID
                head_item.keep=element.count
                lhh_index=column
        elif element_list[column]>element_list[local_max_col]:
        #elif element_list[column]>int((element_list[local_max_col]+head_item.keep)/2):
            # no collision, sk[e_i]>=estimated(sk[LHH]):
            head_item.keep-=element.count
            if head_item.keep<0:
                head_item.maxID=element.ID
                #head_item.keep=int((element_list[local_max_col]+head_item.keep+element.count)/2)
                #head_item.keep=int((element_list[column]+element_list[column]-element_list[local_max_col])/2)
                head_item.keep=element.count
                lhh_index=column
            else:
                lhh_index=local_max_col
    # update e_max
    #lhh_count=element_list[column]
    #if int((element_list[local_max_col]+head_item.keep)/2)>Config.e_max.count:
    #if int((element_list[column]+element_list[column]-element_list[local_max_col])/2)>Config.e_max.count:
    #if (element_list[lhh_index]>>1) >Config.e_max.count:  
    if int((element_list[lhh_index]+head_item.keep)/2)>Config.e_max.count:    
        Config.e_max.ID=element.ID
        Config.e_max.count=int((element_list[lhh_index]+head_item.keep)/2)
        #Config.e_max.count=int((element_list[local_max_col]+head_item.keep)/2)
        #Config.e_max.count=int((element_list[column]+element_list[column]-element_list[local_max_col])/2)

# ========================== BringBack=========================
def BringBack(e_min,Top,head,sketch):
    # bring e_max back to Top
    # e_min=e_max, e_max=Null, delete e_max.count in Sketch, send e_min into Sketch
    Top.pop(e_min.ID)
    Top[Config.e_max.ID]=Config.e_max.count
    DeleteSk(Config.e_max,head,sketch)
    UpdateSk(e_min,head,sketch)
    #col,row=position(DS.Tail(Config.e_max.ID,1))
    
# ==========================DeleteSk=========================
def DeleteSk(element,head,sketch):
    # e_max in sketch: sketch[r][c]=0, total count-=sketch[row][col]
    #width,depth=get_width_depth()
    col,row=positionCS(element,)
    head[row].count-=element.count
        # total_count-=element.count
    sketch[row][col]-=element.count
    head[row].maxID=''
    # reset e_max
    element.ID=""
    element.count=0

def find(e,element_list):
    # return index of e in element_list
    try:
        index=[ele.ID for ele in element_list].index(e.ID)
    except:
        index=-99
    return index

def position(element,index):
    hash1=mmh3.hash(element.ID,seed=Config.seed[index], signed=False)
    pos=hash1 % Config.width
    return pos 


def positionCS(element):
    hash1=mmh3.hash(element.ID,seed=Config.seed[0], signed=False)
    hash2=mmh3.hash(element.ID,seed=Config.seed[1], signed=False)
    col=hash1 % Config.width
    row=hash2 % Config.depth
    return col,row 


def Top_to_csv(Top,dataset_name):
    templi=[[i.ID,i.count] for i in Top]
    df=pd.DataFrame(templi,columns=['ID', 'Count'])
    df=df.sort_values(by='Count',ascending=False)
    name="My_OO_"+dataset_name+"_Top"+'_'+str(Config.size)+'_'+str(Config.depth)+'_'+str(Config.width)+'.csv'
    # My_OO_kosarak_Top_size_d_w.csv" for algorithm result
    df.to_csv(os.path.join(r'..\result',name),index=False)
    print(name)
    return name
    
def Get_precision(ground_truth_path,result_dict,topk):
    #gr_truth: path of csv file
    #print("Top-{}".format(topk))
    grtruth=pd.read_csv(ground_truth_path)
        # ground truth of whole data set, [Element, Count]
    grtruth['Element'] = grtruth['Element'].astype(str)
    # precision
    gt_set=set(grtruth['Element'][:topk])
        # e.ID only
    my_set=set(result_dict.keys())
    tp_set=gt_set & my_set
        # true-positive set
        # &: set 交集運算
    precision=len(tp_set)/topk
        # &: set 交集運算
    
    return tp_set,precision

def Get_ARE_AAE(ground_truth_path,result_dict,tp_set):
    # compare with count in result_dict[:topk] with ground_truth[:topk]
    grtruth=pd.read_csv(ground_truth_path)
        # DF of ground truth of whole data set
    grtruth['Element'] = grtruth['Element'].astype(str)
        # ID transfer to str
    gt_dict=dict(grtruth[:Config.topk].values.tolist())
        # Top-k in ground truth
    # top-k ARE/AAE
    top_are=0
    top_aae=0    
    for item in tp_set:
        top_are+=abs(result_dict[item]-gt_dict[item])/gt_dict[item]
        top_aae+=abs(result_dict[item]-gt_dict[item])
    top_are=top_are/len(tp_set)
    top_aae=top_aae/len(tp_set)

    return top_are,top_aae

def To_df(Top,Sketch,Sk_head,*args):
    (startx,endx,true_positive_set,precision,top_are,top_aae,all_are,all_aae,tp,fp)=args
    sketch_size=str(Config.depth)+'*'+str(Config.width)
    temp=sys.getsizeof(Top)+Sketch.nbytes+sys.getsizeof(Sk_head[0])*Config.depth
    memory_usage=str(temp)+' bytes ='+'Top:'+str(sys.getsizeof(Top))+'+ Sketch:'+str(Sketch.nbytes)+'+ Sk_head:'+str(sys.getsizeof(Sk_head[0])*Config.depth)

    result_df=pd.DataFrame(columns=['Top-k',
                                    'Sketch',
                                    'Total memory',
                                    'Exe_time',
                                    'Find',
                                    'Precision',
                                    'ARE-Top',
                                    'AAE-Top',
                                    'ARE-all',
                                    'AAE-all'])
    output_dict={
        'Top-k':Config.size,
        'Sketch':sketch_size,
        'Total memory':memory_usage,
        'Exe_time':float('{:.3f}'.format(endx-startx)),
        'Find':"Find:{}, TP:{}, FP:{}".format(len(true_positive_set),tp,fp),
        'Precision':float("{:8.4f}".format(precision)),
        'ARE-Top':float('{:8.6f}'.format(top_are)),
        'AAE-Top':float('{:8.6f}'.format(top_aae)),
        'ARE-all':float('{:8.6f}'.format(all_are)),
        'AAE-all':float('{:8.6f}'.format(all_aae))}

    result_df=result_df.append(output_dict,ignore_index=True)
    file="My_OO_kosarak_result"+'_'+str(Config.size)+'_'+str(Config.depth)+'_'+str(Config.width)+'_.csv'
    result_df.to_csv(file,index=False)
    return result_df

        
def Query(e,Top,local_maxID,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    index=find(DS.Tail(e,0),Top)
    if index>=0:
        # e in Top
        count=Top[index].count
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        if e in local_maxID:
            # e is LHH
            count=Sketch[row][col]
        else:
            # e is not LHH
            ratio=Config.width/row_cardinality[row]
            count=int(Sketch[row][col]*ratio)
    if count<=1:
        count=1
    return count    
    
    
def Query2(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/row_cardinality[row]
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
        else:
            # e is not LHH
            count=int((Sketch[row][col]-Sk_head[row].keep)*ratio)
    if count<=1:
        count=1
    return count 
    

def Query3(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    '''
    count=0
    index=find(DS.Tail(e,0),Top)
    if index>=0:
        # e in Top
        count=Top[index].count
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/(row_cardinality[row]-Sk_head[row].bringback)
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
        else:
            # e is not LHH
            lhh_col,lhh_row=position(DS.Tail(Sk_head[row].maxID,0))
            if col==lhh_col:
                count=int((Sketch[row][col]-Sk_head[row].keep)*ratio)
            else:
                count=int(Sketch[row][col]*ratio)
    if count<=1:
        count=1
    return count
    '''
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/row_cardinality[row]
        avg_count=Sk_head[row].count/Config.width
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
        else:
            # e is not LHH
            count=int(avg_count*ratio)
            #count=int((avg_count-Sk_head[row].keep)*ratio)
    if count<=1:
        count=1
    return count         
    

def Query4(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/(row_cardinality[row])
        avg_count=Sk_head[row].count/Config.width
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
            #count=(Sk_head[row].keep+int(Sketch[row][col]*ratio))
        else:
            # e is not LHH
            count=int((avg_count-Sk_head[row].keep)*ratio)
    if count<1:
        count=1
    return count    

def Query5(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # not work for LHH estimation
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        #ratio=Config.width/row_cardinality[row]
        #avg_count=Sk_head[row].count/Config.width
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sketch[row][col]
        else:
            # e is not LHH
            #count=int((avg_count-Sk_head[row].keep)*ratio)
            count=math.ceil(Sk_head[row].count/Config.width)
    if count<1:
        count=1
    return count

def Query6(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/row_cardinality[row]
        avg_count=Sk_head[row].count/row_cardinality[row]
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)/2)+int((Sk_head[row].count-sum(Sketch[row]))/Config.width)
        else:
            # e is not LHH
            estimate=int(Sketch[row][col]*ratio)
            count=int((avg_count+estimate)/2)
    if count<1:
        count=1
    return count        

def Query7(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/row_cardinality[row]
        avg_count=Sk_head[row].count/row_cardinality[row]
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sketch[row][col]
        else:
            # e is not LHH
            count=int((avg_count-Sk_head[row].keep)*ratio)

    if count<1:
        count=1
    return count

def Query8(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=positionCS(DS.Tail(e,0))
        max_col,max_row=positionCS(DS.Tail(Sk_head[row].maxID,0))
        if e == Sk_head[row].maxID:
            # e is LHH
            temp=0
            for i in range(Config.width):
                if Sketch[row][i]>Sketch[row][max_col]:
                    temp+=Sketch[row][i]-Sketch[row][max_col]
            count=int((Sketch[row][col]+Sk_head[row].keep+temp)/2)
            #print("{} is LHH with count {}".format(e,count))
        else:
            # e is not LHH
            count=int((Sketch[row][col]*Config.width)/row_cardinality[row])

            '''
            if count>32:
                print("{} estimated: {}".format(e,count))
                print("Sketch[{}][{}]:{}".format(row,col,Sketch[row][col]))
                print("Config.width:{}".format(Config.width))
                print("row_cardinality[{}]:{}".format(row,row_cardinality[row]))
            if col==max_col:
                # collisin with LHH
                temp=0
                for i in range(Config.width):
                    if Sketch[row][i]>Sketch[row][max_col]:
                        temp+=Sketch[row][i]-Sketch[row][max_col]
                LHHcount=int((Sketch[row][col]+Sk_head[row].keep+temp)/2)                    
                count=int(((Sketch[row][col]-LHHcount)*Config.width)/(row_cardinality[row]-1))
            else:
                count=int(Sketch[row][col]*Config.width/row_cardinality[row])            
            '''
    if count<1:
        count=1
    return count

def Query9(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=positionCS(DS.Tail(e,0))
        ratio=Config.width/row_cardinality[row]
            # avg collision rate
        avg_count=Sk_head[row].count/row_cardinality[row]
            # avg count per cell 
        if e == Sk_head[row].maxID:
            # e is LHH
            if ratio<=1:
                count=int(((Sk_head[row].keep+(Sketch[row][col]-Sk_head[row].keep)*ratio)*(1-ratio)+Sketch[row][col]*(ratio))/2)
            else:
                count=Sketch[row][col]
        else:
            '''
            # Don't care collision with lhh
            # e is not LHH
            count=int((avg_count-Sk_head[row].keep)*ratio)
            
            
            # Split collision with LHH
            # e is not LHH
            maxcol,maxrow=position(DS.Tail(Sk_head[row].maxID,0))
            if col==maxcol:
                # collision with lhh
                count=int(Sketch[row][col]-Sk_head[row].keep)*ratio
            else:
                count=int((Sketch[row][col])*ratio)             
            
            '''
            # Don't care collision with lhh
            # e is not LHH
            #count=int((avg_count-Sk_head[row].keep)*ratio)
            count=int(Sketch[row][col]/row_cardinality[row])
    if count<1:
        count=1
    return count

def Query10(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/row_cardinality[row]
            # avg collision rate
        avg_count=Sk_head[row].count/row_cardinality[row]
            # avg count per cell 
        '''
        if e == Sk_head[row].maxID:
            # e is LHH
            count=(Sketch[row][col]+Sk_head[row].keep+sum([i-Sketch[row][col] for i in Sketch[row] if i>Sketch[row][col]]))/2
        '''   
        if e == Sk_head[row].maxID:
            # e is LHH
            if ratio<=1:
                count=int((Sk_head[row].keep+(Sketch[row][col]-Sk_head[row].keep)*ratio)*(1-ratio)+Sketch[row][col]*(ratio))
            else:
                count=Sketch[row][col]
        else:
            # Don't care collision with lhh
            # e is not LHH
            if ratio<1:
                count=int((Sketch[row][col]*ratio)*(1-ratio)+(avg_count*(ratio)))
            else:
                count=Sketch[row][col]
    if count<1:
        count=1
    return count


def Get_ground_truth(ground_truth_path,topk=None):
    grtruth=pd.read_csv(ground_truth_path)
        # ground truth of whole data set, [Element, Count]
    grtruth['Element'] = grtruth['Element'].astype(str)
        # sorted, not use set.
    gt_dict=dict(grtruth[:topk].values.tolist())
        # top-k e.ID only    
    return gt_dict

def Plot_topk_compare(ground_truth_path,result_dict,method):
    gt_dict=Get_ground_truth(ground_truth_path,Config.topk)
    gr_count=[]
    my_count=[]
    tp_list=[]
    
    for item in gt_dict:
        if item in result_dict:
            tp_list.append(item)
            gr_count.append(gt_dict[item])
            my_count.append(result_dict[item])
            
    # set max y ticks
    max_element=max(gt_dict, key=gt_dict.get)
    y_max=int(np.log2(gt_dict[max_element]))     
    
    indexli=[i for i in range (len(tp_list))]
    plt.figure(figsize=[14,8])
    plt.xticks([j for j in range(0,len(tp_list),50)])
    plt.yticks([j for j in range(0,y_max)])
    plt.xlabel('Top-{}/{}'.format(len(tp_list),Config.topk))
    plt.ylabel('Count, log scale')

    my_line,=plt.plot(indexli,np.log2(my_count),'g.',label=method,alpha=0.5)
    gr_line,=plt.plot(indexli,np.log2(gr_count),'r.',label='GroundTruth',alpha=0.3)

    plt.legend(handles=[gr_line,my_line],loc='best')
    plt.show()
    
def esQuery(e,Top,Skech):
    # Top is a list
    index=position(DS.Tail(e,1),1)
    count=0
    try:
        if Top[index].ID==e:
            if Top[index].flag==False:
                count=Top[index].vote_pos
            else:
                count=Top[index].vote_pos+Skech.Estimate_CMS(DS.Tail(e,1))
        else:
            count=Skech.Estimate_CMS(DS.Tail(e,1))
    except:
        print("KeyError of {}".format(e))
    return count  

def Plot_all_compare(gt_dict,result_dict,method):
    #gt_dict=Get_ground_truth(ground_truth_path)
    #result_dict=dict(sorted(result_dict.items(), key=lambda item: item[1],reverse=True))

    gr_count=[]
    my_count=[]
    for item in gt_dict:
        if item in result_dict:
            gr_count.append(gt_dict[item])
            my_count.append(result_dict[item])
        else:
            my_count.append(1)
    
    # set max y ticks
    max_element=max(gt_dict, key=gt_dict.get)
    y_max=int(np.log2(gt_dict[max_element]))
    
    # Plot Figure
    indexli=[i for i in range (len(gt_dict))]
    
    # Comparison
    plt.figure(figsize=[20,8])
    plt.xticks([j for j in range(0,len(gt_dict),int(len(gt_dict)/20))])
    plt.yticks([j for j in range(0,y_max)])
    plt.xlabel('Top-k Element sorted by count')    
    plt.ylabel('Count, log scale')
    my_line,=plt.plot(indexli,np.log2(list(result_dict.values())),'g.',label=method,alpha=0.5)
    gr_line,=plt.plot(indexli,np.log2(list(gt_dict.values())),'r.',label='GroundTruth',alpha=0.3)
    plt.legend(handles=[gr_line,my_line],loc='best')
    plt.show()
    
    
    # Ground Truth
    plt.figure(figsize=[20,8])
    plt.xticks([j for j in range(0,len(gt_dict),int(len(gt_dict)/20))])
    plt.yticks([j for j in range(0,y_max)])
    #plt.xlabel('Top-{}/{}'.format(len(tp_list),Config.topk))
    plt.xlabel('Top-k Element sorted by count')    
    plt.ylabel('Count, log scale')
    #my_line,=plt.plot(indexli,np.log2(list(result_dict.values())),'g.',label='Cyclic Sketch',alpha=0.5)
    gr_line,=plt.plot(indexli,np.log2(list(gt_dict.values())),'r.',label='GroundTruth',alpha=0.3)

    #plt.legend(handles=[gr_line,my_line],loc='best')
    plt.legend(handles=[gr_line],loc='best')
    plt.show()
    
    # Algo result
    plt.figure(figsize=[20,8])
    #plt.xlabel('Top-{}/{}'.format(len(tp_list),Config.topk))
    plt.xticks([j for j in range(0,len(gt_dict),int(len(gt_dict)/20))])
    plt.yticks([j for j in range(0,y_max)])
    plt.xlabel('Top-k Element')    
    plt.ylabel('Count, log scale')
    my_line,=plt.plot(indexli,np.log2(list(result_dict.values())),'g.',label=method,alpha=0.5)
    plt.legend(handles=[my_line],loc='best')
    plt.show()
    
    #return gr_count,my_count
    
    
def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))    