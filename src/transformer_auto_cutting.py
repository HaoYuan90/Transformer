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
normal_tolerance = 0.03
# Number of divisions 
tier_1_divs = 20 #20
tier_2_divs = 10
tier_3_divs = 10
# How accurate the accepted cuts are
allowed_pd_volume = 0.1
allowed_pd_aspect = 0.2

# Debug messages control
DEBUG_MATCHING = False

"""
Copy a blender obj, copy operator is buggy
Takes in original_object, name of copied object
Return copied object
"""
def copy_object(orig_obj, to_obj_name):
    temp_mesh = bpy.data.meshes.new('SomeNameThatDoesntMatter')
    copy = bpy.data.objects.new(to_obj_name, temp_mesh)
    copy.data = orig_obj.data.copy()
    copy.data.name = to_obj_name
    copy.location = orig_obj.location
    copy.scale = orig_obj.scale
    copy.rotation_euler = orig_obj.rotation_euler
    bpy.context.scene.objects.link(copy)
    
    bpy.data.meshes.remove(temp_mesh)
    return copy

"""
Return the 8 vertices of a cuboid constructed from  constrains of 3 dimensions
"""
def generate_cuboid_verts(x_max,x_min,y_max,y_min,z_max,z_min):
    verts = []
    verts.append((x_min,y_max,z_max))
    verts.append((x_max,y_max,z_max))
    verts.append((x_min,y_max,z_min))
    verts.append((x_max,y_max,z_min))
    verts.append((x_min,y_min,z_max))
    verts.append((x_max,y_min,z_max))
    verts.append((x_min,y_min,z_min))
    verts.append((x_max,y_min,z_min))
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
    bpy.ops.object.mode_set(mode = 'OBJECT')
    obj_to.select = False
    
    
"""
Get area of cut surfaces for volume approximation
"""
def get_cut_surfaces_area(vertices,polygons,dim_string,near_plane,far_plane,interval):
    # Determine dimension
    dim = 0
    if dim_string == "x":
        dim = 0
    elif dim_string == "y":
        dim = 1
    elif dim_string == "z":
        dim = 2
    else:
        return 0
    
    """
    In here, average plane is checked against a threshold to take into account of
    hollowed object, the hollowed face, if its normal is just right, should not be
    counted to make the estimated volume even larger than it already is
    """
    area = 0
    far_threshold = far_plane - interval/10
    near_threshold = near_plane + interval/10
    for face in polygons:
        # Facing towards positive axis
        if math.fabs(face.normal[dim]-1)<= normal_tolerance:
            average_plane = 0
            for vert in face.vertices:
                average_plane += vertices[vert].co[dim]
            average_plane = average_plane/len(face.vertices)
            if average_plane >= far_threshold:
                area = area+face.area*(average_plane-near_plane)/interval
        # Facing towards negative axis
        elif math.fabs(face.normal[dim]+1) <= normal_tolerance:
            average_plane = 0
            for vert in face.vertices:
                average_plane += vertices[vert].co[dim]
            average_plane = average_plane/len(face.vertices)
            if average_plane <= near_threshold:
                area = area+face.area*(far_plane-average_plane)/interval
    return area

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
Pad the print message in verify cut with appropriate number of '*'
"""
def pad_msg(div_id):
    if div_id.count('_') == 0:
        return "****************"
    elif div_id.count('_') == 1:
        return "********"
    else:
        return ""
        
"""
Verify if a cut can be accepted based on its volume ratio and aspect ratio
temp_sto is a dictionary containing some values to be written back to the cut
Return BOOLEAN
"""
def verify_cut(div_id, req_volume_ratio, req_aspects, estimated_volume, dim_x, dim_y, dim_z, temp_sto):
    
    # Matching volume 
    if DEBUG_MATCHING:
        print("{} matching {}".format(pad_msg(div_id), div_id))
        print("{} volume req/act : {} / {}".format(pad_msg(div_id), req_volume_ratio, estimated_volume))

    if not arith.percentage_discrepancy(estimated_volume, req_volume_ratio) <= allowed_pd_volume:
        if DEBUG_MATCHING:
            print("{} rejected".format(pad_msg(div_id)))
            print()
        temp_sto['pd'] = -1
        return False
    
    # Matching aspect ratio    
    aspect_ratio_satisfied = False
    
    configure_1 = []
    configure_1.append(dim_x/dim_y)
    configure_1.append(dim_z/dim_y)
    configure_2 = []
    configure_2.append(dim_y/dim_x)
    configure_2.append(dim_z/dim_x)
    configure_3 = []
    configure_3.append(dim_x/dim_z)
    configure_3.append(dim_y/dim_z)
    
    if DEBUG_MATCHING:
        print("{} aspect ratio req : {}".format(pad_msg(div_id), req_aspects))
        print("{} aspect ratio 1/2/3 : {} / {} / {}".format(pad_msg(div_id), configure_1, configure_2, configure_3))
    
    # The smallest percentage difference possible
    pds = {arith.percentage_discrepancy(configure_1[0], req_aspects[0]) + arith.percentage_discrepancy(configure_1[1], req_aspects[1]),\
           arith.percentage_discrepancy(configure_1[1], req_aspects[0]) + arith.percentage_discrepancy(configure_1[0], req_aspects[1]),\
           arith.percentage_discrepancy(configure_2[0], req_aspects[0]) + arith.percentage_discrepancy(configure_2[1], req_aspects[1]),\
           arith.percentage_discrepancy(configure_2[1], req_aspects[0]) + arith.percentage_discrepancy(configure_2[0], req_aspects[1]),\
           arith.percentage_discrepancy(configure_3[0], req_aspects[0]) + arith.percentage_discrepancy(configure_3[1], req_aspects[1]),\
           arith.percentage_discrepancy(configure_3[1], req_aspects[0]) + arith.percentage_discrepancy(configure_3[0], req_aspects[1])}
    pd = min(pds)
    temp_sto['pd'] = pd
    
    if (arith.percentage_discrepancy(configure_1[0], req_aspects[0]) <= allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_1[1], req_aspects[1]) <= allowed_pd_aspect) \
    or (arith.percentage_discrepancy(configure_1[1], req_aspects[0]) <= allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_1[0], req_aspects[1]) <= allowed_pd_aspect):
        aspect_ratio_satisfied = True
    
    if (arith.percentage_discrepancy(configure_2[0], req_aspects[0]) <= allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_2[1], req_aspects[1]) <= allowed_pd_aspect) \
    or (arith.percentage_discrepancy(configure_2[1], req_aspects[0]) <= allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_2[0], req_aspects[1]) <= allowed_pd_aspect):
        aspect_ratio_satisfied = True
        
    if (arith.percentage_discrepancy(configure_3[0], req_aspects[0]) <= allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_3[1], req_aspects[1]) <= allowed_pd_aspect) \
    or (arith.percentage_discrepancy(configure_3[1], req_aspects[0]) <= allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_3[0], req_aspects[1]) <= allowed_pd_aspect):
        aspect_ratio_satisfied = True
    
    if not aspect_ratio_satisfied:
        if DEBUG_MATCHING:
            print("{} rejected".format(pad_msg(div_id)))
            print()
        return False
    
    if DEBUG_MATCHING:
        print("{} accepted".format(pad_msg(div_id)))
        print()
    return True


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
            
"""
Remove all intermediate objects created
and flush all associated meshes
"""
def intermediate_cleanup():
    objects = bpy.data.objects
    for obj in objects:
        obj.select = False
        if "division" in obj.name or "assist" in obj.name:
            obj.select = True
    bpy.ops.object.delete()
    for mesh in bpy.data.meshes:
        if "division" in mesh.name or "assist" in mesh.name:
            bpy.data.meshes.remove(mesh)
            
"""
Remove all potential cuts, leaving the best
and flush all associated meshes
"""
def tier_end_cleanup():
    objects = bpy.data.objects
    first_obj = None
    for obj in objects:
        if "potential" in obj.name and obj['pd'] != -1:
            first_obj = obj
            break
        
    if first_obj == None:
        return
    
    best_cut = first_obj
    min_pd = first_obj['pd']
    
    # Get the best potential cut
    for obj in objects:
        if "potential" in obj.name and obj['pd'] != -1:
            if obj['pd'] < min_pd:
                min_pd = obj['pd']
                best_cut = obj
        
    # Remove all non-intermediate potential cuts except for the best
    mesh_to_remove = []
    for obj in objects:
        obj.select = False
        if "potential" in obj.name and obj != best_cut:
            mesh_to_remove.append(obj.name)
            obj.select = True
    bpy.ops.object.delete()
    for mesh in bpy.data.meshes:
        if mesh.name in mesh_to_remove:
            bpy.data.meshes.remove(mesh)
            
            
    
def autocut_main(req_volume_ratio, req_aspect_ratio):
    req_aspects = []
    req_aspects.append(req_aspect_ratio[0]/req_aspect_ratio[1])
    req_aspects.append(req_aspect_ratio[2]/req_aspect_ratio[1])
    
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
    # The bigger box surrounding the object to facilitate boolean operation
    x_max_box = x_max + x_temp
    x_min_box = x_min - x_temp
    z_max_box = z_max + z_temp
    z_min_box = z_min - z_temp

    this_y = y_min
    obj.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,tier_1_divs):  
        y_near = this_y
        this_y = this_y + y_interval
        y_far = this_y
        name = str.format("division_{}", i+1)
        cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_far,y_near,z_max_box,z_min_box),name)
        
        perform_boolean_operation(obj,cuboid,"INTERSECT")
       
        divisions.append(cuboid)
                    
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"y",y_near,y_far,y_interval))
    
    volume_ratios = get_volume_ratios(cutsurface_areas)
    
    #print("tier 1 cutsurface_areas")
    #print(cutsurface_areas)
    #print("tier 1 volume_ratios")
    #print(volume_ratios)
    
    analysis.analyse_volume_approximation(obj, divisions, volume_ratios)
    
    intermediate_cleanup()
    
    if DEBUG_MATCHING:
        print("**************** Tier 1 matching starts")
        print()
    # Find a cut with volume just bigger than required volume
    y_near = y_min
    y_far = y_near
    accumulated_volume_ratio = 0
    cut_id = 1
    temp_sto = {'pd':-1}
    for i in range(0,tier_1_divs):  
        div_id = str.format("{}", cut_id)
        accumulated_volume_ratio += volume_ratios[i]
        if accumulated_volume_ratio > req_volume_ratio:
            y_far = y_near + (i+1)*y_interval
            if verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,x_max-x_min,y_far-y_near,z_max-z_min,temp_sto):
                name = str.format("accepted_cut_{}", cut_id)
                tier_1_cut = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_far,y_near,z_max_box,z_min_box),name)
                perform_boolean_operation(obj,tier_1_cut,"INTERSECT")
                tier_1_cut['pd'] = temp_sto['pd']
            else:
                name = str.format("potential_cut_{}", cut_id)
                tier_1_cut = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_far,y_near,z_max_box,z_min_box),name)
                perform_boolean_operation(obj,tier_1_cut,"INTERSECT")
                tier_1_cut['pd'] = temp_sto['pd']
                tier_2_matching(cut_id, tier_1_cut, req_volume_ratio/accumulated_volume_ratio, req_aspects)
                #tier_3_matching(cut_id, cut_id, tier_1_cut, req_volume_ratio/accumulated_volume_ratio, req_aspects)
                
        elif arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= allowed_pd_volume:
            y_far = y_near + (i+1)*y_interval
            if verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,x_max-x_min,y_far-y_near,z_max-z_min,temp_sto):
                name = str.format("accepted_cut_{}", cut_id)
                tier_1_cut = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_far,y_near,z_max_box,z_min_box),name)
                perform_boolean_operation(obj,tier_1_cut,"INTERSECT")
                tier_1_cut['pd'] = temp_sto['pd']
                
        cut_id += 1
           
    if DEBUG_MATCHING:     
        print("**************** Tier 1 matching ends")
        print()
    

def tier_2_matching(tier_1_id, tier_1_cut, req_volume_ratio, req_aspects):
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
    
    # 2nd division is along x-axis
    x_interval = (x_max-x_min)/tier_2_divs
    y_temp = (y_max-y_min)/tier_2_divs
    z_temp = (z_max-z_min)/tier_2_divs
    y_max_box = y_max + y_temp
    y_min_box = y_min - y_temp
    z_max_box = z_max + z_temp
    z_min_box = z_min - z_temp

    this_x = x_min
    tier_1_cut.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,tier_2_divs):  
        x_near = this_x
        this_x = this_x + x_interval
        x_far = this_x
        name = str.format("division_{}", i+1)
        cuboid = create_cuboid(generate_cuboid_verts(x_far,x_near,y_max_box,y_min_box,z_max_box,z_min_box,),name)
        
        perform_boolean_operation(tier_1_cut,cuboid,"INTERSECT")
       
        divisions.append(cuboid)
        
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"x",x_near,x_far,x_interval))
        
    volume_ratios = get_volume_ratios(cutsurface_areas)
    
    #print("tier 2 volume_ratios")
    #print(volume_ratios)
    #print("tier 2 cutsurface_areas")
    #print(cutsurface_areas)
    
    analysis.analyse_volume_approximation(tier_1_cut, divisions, volume_ratios)
    
    intermediate_cleanup()
    
    if DEBUG_MATCHING:
        print("******** Tier 2 matching of div {}".format(tier_1_id))
        print()
        
    # Find a cut with volume just bigger than required volume (symmetric case)
    x_near = x_min
    x_far = x_near
    accumulated_volume_ratio = 0
    cut_id = 1
    temp_sto = {'pd':-1}
    for i in range(0,math.floor(tier_2_divs/2)-1):  
        accumulated_volume_ratio += volume_ratios[i]
        accumulated_volume_ratio += volume_ratios[tier_2_divs-1-i]
        div_id = str.format("{}_{}", tier_1_id, cut_id)
        if arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= allowed_pd_volume:
            x_near = x_min + (i+1)*x_interval
            x_far = x_max - (i+1)*x_interval
            if verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,(x_max-x_min)-(x_far-x_near),y_max-y_min,z_max-z_min,temp_sto):
                name = str.format("accepted_cut_{}", div_id)
                tier_1_copy = copy_object(tier_1_cut,name)
                tier_2_assist = create_cuboid(generate_cuboid_verts(x_far,x_near,y_max_box,y_min_box,z_max_box,z_min_box),"tier_2_assist")
                perform_boolean_operation(tier_2_assist,tier_1_copy,"DIFFERENCE")
                tier_1_copy['pd'] = temp_sto['pd']
                intermediate_cleanup()
            else:
                name = str.format("potential_cut_{}", div_id)
                tier_1_copy = copy_object(tier_1_cut,name)
                tier_2_assist = create_cuboid(generate_cuboid_verts(x_far,x_near,y_max_box,y_min_box,z_max_box,z_min_box),"tier_2_assist")
                perform_boolean_operation(tier_2_assist,tier_1_copy,"DIFFERENCE")
                tier_1_copy['pd'] = temp_sto['pd']
                intermediate_cleanup()
                # Invoke tier 3
        cut_id += 1
        
    tier_end_cleanup()
                
    if DEBUG_MATCHING:     
        print("******** Tier 2 matching of div {} ends".format(tier_1_id))
        print()

def tier_3_matching(tier_1_id, tier_2_id, tier_2_cut, req_volume_ratio, req_aspects):
    # Get bound_box of object
    boundbox_verts = []
    for i in tier_2_cut.bound_box:
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
    
    # 3rd division is along z-axis
    z_interval = (z_max-z_min)/tier_3_divs
    x_temp = (x_max-x_min)/tier_3_divs
    y_temp = (y_max-y_min)/tier_3_divs
    x_max_box = x_max + x_temp
    x_min_box = x_min - x_temp
    y_max_box = y_max + y_temp
    y_min_box = y_min - y_temp

    this_z = z_min
    tier_2_cut.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,tier_3_divs):  
        z_near = this_z
        this_z = this_z + z_interval
        z_far = this_z
        name = str.format("division_{}", i+1)
        cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_near),name)
        
        perform_boolean_operation(tier_2_cut,cuboid,"INTERSECT")
       
        divisions.append(cuboid)
                    
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"z",z_near,z_far,z_interval))
        
    volume_ratios = get_volume_ratios(cutsurface_areas)
    
    #print("tier 3 volume_ratios")
    #print(volume_ratios)
    #print("tier 3 cutsurface_areas")
    #print(cutsurface_areas)
    
    analysis.analyse_volume_approximation(tier_2_cut, divisions, volume_ratios)
    
    intermediate_cleanup()
    
    if DEBUG_MATCHING:
        print("Tier 3 matching of div {}_{}".format(tier_1_id, tier_2_id))
        print()
    
    # Find acceptable cut
    z_near = z_min
    z_far = z_near
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in range(0,tier_3_divs):  
        accumulated_volume_ratio += volume_ratios[i]   
        div_id = str.format("{}_{}_{}",tier_1_id,tier_2_id,cut_id)  
        if arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= allowed_pd_volume:
            z_far = z_near + (i+1)*z_interval
            if verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,x_max-x_min,y_max-y_min,z_far-z_near):
                name = str.format("accepted_cut_{}_{}_{}", tier_1_id, tier_2_id, cut_id)
                tier_3_cut = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_near),name)
                perform_boolean_operation(tier_2_cut,tier_3_cut,"INTERSECT")
        cut_id += 1
                
    if DEBUG_MATCHING:     
        print("Tier 3 matching of div {}_{} ends".format(tier_1_id, tier_2_id))
        print()

            
            
            
            
            
            