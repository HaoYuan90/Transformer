import math

""" Get sum of items in a list """
def summation(x):
    result = 0;
    for i in x:
        result += i
    return result

""" Get sum of items squared in a list (1^2+2^2+.....)"""
def squared_sum(x):
    squared_x = []
    for i in x:
        squared_x.append(math.pow(i,2))
    
    return summation(squared_x)
    
""" 
    Get sum of items multiplied to each other in 2 lists (xy+xy+.....)
    Length of lists have to be the same
"""
def mult_sum(x,y):
    xy = []
    for i in range(len(x)):
        xy.append(x[i]*y[i])
    return summation(xy)

def percentage_discrepancy(est,real):
    return math.fabs(real-est)/real