import math

"""
3D vectors
"""
""" Vector addition """
def vecadd(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] + b[2]]

""" Vector substration """
def vecsub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]

""" Vector crossproduct """
def veccross(x, y):
    v = [0, 0, 0]
    v[0] = x[1]*y[2] - x[2]*y[1]
    v[1] = x[2]*y[0] - x[0]*y[2]
    v[2] = x[0]*y[1] - x[1]*y[0]
    return v

""" Vector dotproduct """
def vecdot(x, y):
    return x[0]*y[0] + x[1]*y[1] + x[2]*y[2]

""" Vector length """
def length(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

""" Vector multiplied by constant s"""
def vecmul(a, s):
    return[a[0]*s, a[1]*s, a[2]*s]

