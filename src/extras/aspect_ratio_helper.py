"""
Get real aspect ratio of an object
"""

"""
import sys

mypath = "C:\\Users\\Xiaopewpew\\Desktop\\GithubProjects\\Transformer\\src\\extras"
sys.path.append(mypath)

src_path = "C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/src/extras/aspect_ratio_helper.py"
exec(compile(open(src_path).read(), "src_path", 'exec'))

box = C.active_object.bound_box
get_aspect_ratio(box)
"""
import bpy

def get_aspect_ratio(boundbox):
    boundbox_verts = []
    for i in boundbox:
        boundbox_verts.append(i)

    x_min = boundbox_verts[0][0]
    x_max = boundbox_verts[0][0]
    y_min = boundbox_verts[0][1]
    y_max = boundbox_verts[0][1]
    z_min = boundbox_verts[0][2]
    z_max = boundbox_verts[0][2]
    for i in boundbox_verts:
        if i[0] > x_max:
            x_max = i[0]
        if i[0] < x_min:
            x_min = i[0]
        if i[1] > y_max:
            y_max = i[1]
        if i[1] < y_min:
            y_min = i[1]
        if i[2] > z_max:
            z_max = i[2]
        if i[2] < z_min:
            z_min = i[2]
    
    return (x_max-x_min,y_max-y_min,z_max-z_min)
    