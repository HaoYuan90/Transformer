'''
@author: Jiang HaoYuan, National University of Singapore
'''

import bpy
import bmesh

import math
import vector_helper as vector
import arithmetic_helper as arith
import analysis_helper as analysis

"""
Copy a blender obj, copy operator is buggy
Takes in original_object, name of copied object
Return copied object
"""
def copy_object(orig_obj, to_obj_name):
    copy = bpy.data.objects.new(to_obj_name, bpy.data.meshes.new(to_obj_name))
    copy.data = orig_obj.data.copy()
    copy.location = orig_obj.location
    copy.scale = orig_obj.scale
    copy.rotation_euler = orig_obj.rotation_euler
    bpy.context.scene.objects.link(copy)
    return copy

"""
Return the 8 vertices of a cuboid constructed from  constrains of 3 dimensions
"""
def generate_cuboid_verts_y(x_max,x_min,z_max,z_min,y_far,y_near):
    verts = []
    verts.append((x_min,y_far,z_max))
    verts.append((x_max,y_far,z_max))
    verts.append((x_min,y_far,z_min))
    verts.append((x_max,y_far,z_min))
    verts.append((x_min,y_near,z_max))
    verts.append((x_max,y_near,z_max))
    verts.append((x_min,y_near,z_min))
    verts.append((x_max,y_near,z_min))
    return verts

"""
Create a cubic blender object
Takes in 8 vertices of cuboid and name of the object
Return the object created
"""
def create_cuboid(verts, name):
    cuboid_verts = verts
    cuboid_faces = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(1,5,7,3),(4,0,2,6),(6,2,3,7)]
    cuboid_mesh = bpy.data.meshes.new(name)
    cuboid = bpy.data.objects.new(name, cuboid_mesh)
    bpy.context.scene.objects.link(cuboid)
    cuboid_mesh.from_pydata(cuboid_verts, [], cuboid_faces)
    cuboid_mesh.update(calc_edges=True)
    return cuboid


def get_volume_ratios(cut_surface_areas):
    volume_ratios = []
    area_sum = math.fsum(cut_surface_areas)
    for area in cut_surface_areas:
        volume_ratios.append(area/area_sum)
    return volume_ratios

def autocut_main():
    # Floating point error tolerance
    fp_tolerance = 0.0001
    obj = bpy.context.active_object
    
    # Get bound_box of object
    boundbox_verts = []
    for i in obj.bound_box:
        boundbox_verts.append(i)
        
    # plug in PCA here if needed, perform pca, rotate object and save the rotation
    
    # Get bound coordinates of the object
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
    
    # First division is along y-axis
    num_divs = 10
    y_interval = (y_max-y_min)/num_divs
    x_temp = (x_max-x_min)/10
    z_temp = (z_max-z_min)/10
    x_max = x_max + x_temp
    x_min = x_min - x_temp
    z_max = z_max + z_temp
    z_min = z_min - z_temp

    this_y = y_min
    obj.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,10):  
        y_near = this_y
        this_y = this_y + y_interval
        y_far = this_y
        name = str.format("division_{}", i+1)
        cuboid = create_cuboid(generate_cuboid_verts_y(x_max,x_min,z_max,z_min,y_far,y_near),name)
        
        # Set cuboid to be current active object
        cuboid.select = True
        bpy.context.scene.objects.active = cuboid
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.object.mode_set(mode = 'EDIT')
        """
        subdivide cuboid here, how to determine no of iterations of subdivision?...
        bpy.ops.mesh.subdivide()
        """
        bpy.ops.object.editmode_toggle()
        
        # Apply intersect to obtain the cut
        bpy.ops.object.modifier_add(type='BOOLEAN')
        intersect_mod = cuboid.modifiers['Boolean']
        intersect_mod.operation = 'INTERSECT'
        intersect_mod.object = obj
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=intersect_mod.name)
        
        # Deselect this cuboid
        cuboid.select = False
        divisions.append(cuboid)
        
        # Calculate area of cut surface
        area = 0
        for face in cuboid.data.polygons:
            if math.fabs(face.normal[1]-1)<= fp_tolerance or math.fabs(face.normal[1]+1) <= fp_tolerance:
                is_cut_surface = False
                for vert in face.vertices:
                    if math.fabs(cuboid.data.vertices[vert].co[1]-y_near) <= fp_tolerance or math.fabs(cuboid.data.vertices[vert].co[1]-y_far) <= fp_tolerance:
                        is_cut_surface = True
                if is_cut_surface:
                    area = area+face.area
                    
        cutsurface_areas.append(area)
    
    print(cutsurface_areas)
    volume_ratios = get_volume_ratios(cutsurface_areas)
    
    #analysis.analyse_volume_approximation(obj, divisions, volume_ratios)
        
    return volume_ratios
        
        
        
        
        
        
            
            
            
            
            
            