import math

"""
3D vectors
"""
""" Vector addition """
def vecadd(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] + b[2])

""" Vector substration """
def vecsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

""" Vector crossproduct """
def veccross(x, y):
    return (x[1]*y[2] - x[2]*y[1],x[2]*y[0] - x[0]*y[2],x[0]*y[1] - x[1]*y[0])

""" Vector dotproduct """
def vecdot(x, y):
    return x[0]*y[0] + x[1]*y[1] + x[2]*y[2]

""" Vector length """
def length(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

""" Vector multiplied by constant s"""
def vecmul(a, s):
    return(a[0]*s, a[1]*s, a[2]*s)

""" Normalize vector """
def vecnorm(v):
    if length(v) != 0:
        return vecmul(v,1/length(v))
    else:
        return (0,0,0)

""" Get angle between 2 vectors"""
def vecangle(x,y):
    """
    # Help with debugging
    v1 = [102,-1,50]
    v2 = [24,12,53]
    """
    x_len = length(x)
    y_len = length(y)
    if x_len == 0 or y_len == 0:
        print ("Invalid 0 vector.")
        return
    angle = math.acos(vecdot(x,y)/(x_len*y_len))
    """
    # Help with debugging
    angle = angle/math.pi*180
    print(angle)
    """
    return angle
    

