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
Global constants
"""
# Floating point error tolerance
fp_tolerance = 0.0001
tier_1_divs = 20
tier_2_divs = 20
tier_3_divs = 5
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

"""
Perform blender's boolean operation
obj_from is the object parameter in boolean operation
obj_to is the object which operator is applied to
"""
def perform_boolean_operation(obj_from, obj_to, op_type):
    # Set obj_to to be current active object
    obj_to.select = True
    bpy.context.scene.objects.active = obj_to
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.object.mode_set(mode = 'EDIT')
    """
    subdivide cuboid here, how to determine no of iterations of subdivision?...
    bpy.ops.mesh.subdivide()
    """
    bpy.ops.object.editmode_toggle()
    
    # Apply intersect to obtain the cut
    bpy.ops.object.modifier_add(type='BOOLEAN')
    intersect_mod = obj_to.modifiers['Boolean']
    intersect_mod.operation = op_type
    intersect_mod.object = obj_from
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=intersect_mod.name)
    
    # Deselect this obj_to
    obj_to.select = False

"""
Get estimated volume ratios based on surface area ratios
"""
def get_volume_ratios(cut_surface_areas):
    volume_ratios = []
    area_sum = math.fsum(cut_surface_areas)
    for area in cut_surface_areas:
        volume_ratios.append(area/area_sum)
    return volume_ratios

"""
Remove all objects created
and flush all associated meshes
"""
def autocut_cleanup(): 
    objects = bpy.data.objects
    for obj in objects:
        obj.select = False
        if "division" in obj.name or "cut" in obj.name or "assist" in obj.name:
            obj.select = True
    bpy.ops.object.delete()
    for mesh in bpy.data.meshes:
        if "division" in mesh.name or "cut" in mesh.name or "assist" in mesh.name:
            bpy.data.meshes.remove(mesh)

def autocut_main(req_volume):
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
    y_interval = (y_max-y_min)/tier_1_divs
    x_temp = (x_max-x_min)/tier_1_divs
    z_temp = (z_max-z_min)/tier_1_divs
    x_max = x_max + x_temp
    x_min = x_min - x_temp
    z_max = z_max + z_temp
    z_min = z_min - z_temp

    this_y = y_min
    obj.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,tier_1_divs):  
        y_near = this_y
        this_y = this_y + y_interval
        y_far = this_y
        name = str.format("division_{}", i+1)
        cuboid = create_cuboid(generate_cuboid_verts_y(x_max,x_min,z_max,z_min,y_far,y_near),name)
        
        perform_boolean_operation(obj,cuboid,"INTERSECT")
       
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
    
    print("tier 1 cutsurface_areas")
    print(cutsurface_areas)
    volume_ratios = get_volume_ratios(cutsurface_areas)
    print("tier 1 volume_ratios")
    print(volume_ratios)
    
    #analysis.analyse_volume_approximation(obj, divisions, volume_ratios)
    
    autocut_cleanup()
    
    # Find a cut with volume just bigger than required volume
    y_near = y_min
    y_far = y_near
    accumulated_volume_ratio = 0
    for i in range(0,tier_1_divs):  
        accumulated_volume_ratio += volume_ratios[i]
        if accumulated_volume_ratio > req_volume:
            y_far = y_near + (i+1)*y_interval
            break
    
    tier_1_cut = create_cuboid(generate_cuboid_verts_y(x_max,x_min,z_max,z_min,y_far,y_near),"cut")
    perform_boolean_operation(obj,tier_1_cut,"INTERSECT")
    
    return tier_2_matching(tier_1_cut,req_volume)
        
def tier_2_matching(tier_1_cut, req_volume):
    # Get bound_box of object
    boundbox_verts = []
    for i in tier_1_cut.bound_box:
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
    x_interval = (x_max-x_min)/tier_2_divs
    y_temp = (y_max-y_min)/tier_2_divs
    z_temp = (z_max-z_min)/tier_2_divs
    y_max = y_max + y_temp
    y_min = y_min - y_temp
    z_max = z_max + z_temp
    z_min = z_min - z_temp

    this_x = x_min
    tier_1_cut.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,tier_2_divs):  
        x_near = this_x
        this_x = this_x + x_interval
        x_far = this_x
        name = str.format("division_{}", i+1)
        cuboid = create_cuboid(generate_cuboid_verts_y(x_far,x_near,z_max,z_min,y_max,y_min),name)
        
        perform_boolean_operation(tier_1_cut,cuboid,"INTERSECT")
       
        divisions.append(cuboid)
        
        # Calculate area of cut surface
        area = 0
        for face in cuboid.data.polygons:
            if math.fabs(face.normal[0]-1)<= fp_tolerance or math.fabs(face.normal[0]+1) <= fp_tolerance:
                is_cut_surface = False
                for vert in face.vertices:
                    if math.fabs(cuboid.data.vertices[vert].co[0]-x_near) <= fp_tolerance or math.fabs(cuboid.data.vertices[vert].co[0]-x_far) <= fp_tolerance:
                        is_cut_surface = True
                if is_cut_surface:
                    area = area+face.area
                    
        cutsurface_areas.append(area)
    
    print("tier 2 cutsurface_areas")
    print(cutsurface_areas)
    volume_ratios = get_volume_ratios(cutsurface_areas)
    print("tier 2 volume_ratios")
    print(volume_ratios)
    
    #analysis.analyse_volume_approximation(obj, divisions, volume_ratios)
    
    #autocut_cleanup()
    
    # Find a cut with volume just bigger than required volume
    x_near = x_min
    x_far = x_near
    accumulated_volume_ratio = 0
    for i in range(0,math.floor(tier_2_divs/2)):  
        accumulated_volume_ratio += volume_ratios[i]
        accumulated_volume_ratio += volume_ratios[tier_2_divs-1-i]
        print(accumulated_volume_ratio)
        if accumulated_volume_ratio > req_volume:
            print(i)
            x_near = x_min + (i+1)*x_interval
            x_far = x_max - (i+1)*x_interval
            break
    
    tier_2_cut = create_cuboid(generate_cuboid_verts_y(x_far,x_near,z_max,z_min,y_max,y_min),"tier_2_assist")
    perform_boolean_operation(tier_2_cut,tier_1_cut,"DIFFERENCE")
    
    return tier_2_cut
        
        
        
            
            
            
            
            
            