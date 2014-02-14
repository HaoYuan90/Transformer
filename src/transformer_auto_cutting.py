'''
@author: Jiang HaoYuan, National University of Singapore
'''

import bpy
import bmesh

import math
import random
import vector_helper as vector
import arithmetic_helper as arith
import analysis_helper as analysis
from TransformerLogger import TransformerLogger

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
# Deal with blender's bug with boolean operation, choose appropriate ones 
tier_1_subdivision_level = 1
tier_2_subdivision_level = 1
tier_3_subdivision_level = 1
# How accurate the accepted cuts are
allowed_pd_volume = 0.1
allowed_pd_aspect = 0.2
mediocre_pd_cap = 0.8
bad_pd_cap = 1.5

# Logger
logger = TransformerLogger()
# Debug messages control
DEBUG_MATCHING = True

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
level is the level of subdivision
"""
def perform_boolean_intersection(obj_from, obj_to, level):
    # Set obj_to to be current active object
    obj_to.select = True
    bpy.context.scene.objects.active = obj_to
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    bpy.ops.mesh.subdivide(number_cuts = level)
    
    bpy.ops.object.editmode_toggle()
    
    # Apply intersect to obtain the cut
    bpy.ops.object.modifier_add(type='BOOLEAN')
    intersect_mod = obj_to.modifiers['Boolean']
    intersect_mod.operation = "INTERSECT"
    intersect_mod.object = obj_from
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=intersect_mod.name)
    
    # Remove doubles
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.remove_doubles()
    
    # Deselect this obj_to
    bpy.ops.object.mode_set(mode = 'OBJECT')
    obj_to.select = False
    
def perform_boolean_difference(obj_from, obj_to, level):
    # Subdivide obj_from
    obj_from.select = True
    bpy.context.scene.objects.active = obj_from
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.subdivide(number_cuts = level)
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.mode_set(mode = 'OBJECT')
    obj_from.select = False
    
    # Set obj_to to be current active object
    obj_to.select = True
    bpy.context.scene.objects.active = obj_to
    
    # Apply intersect to obtain the cut
    bpy.ops.object.modifier_add(type='BOOLEAN')
    intersect_mod = obj_to.modifiers['Boolean']
    intersect_mod.operation = "DIFFERENCE"
    intersect_mod.object = obj_from
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=intersect_mod.name)
    
    # Remove doubles
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.remove_doubles()
    
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
def verify_cut(div_id, req_volume_ratio, req_aspects, estimated_volume, cut, is_sym):
    # Matching volume 
    if DEBUG_MATCHING:
        logger.add_matching_log("{} matching {}".format(pad_msg(div_id), div_id))
        logger.add_matching_log("{} volume req/act : {} / {}".format(pad_msg(div_id), req_volume_ratio, estimated_volume))

    if not arith.percentage_discrepancy(estimated_volume, req_volume_ratio) <= allowed_pd_volume:
        if DEBUG_MATCHING:
            logger.add_matching_log("{} rejected".format(pad_msg(div_id)))
            logger.add_matching_log("")
        cut['pd'] = -1
        return False
    
    # Matching aspect ratio    
    aspect_ratio_satisfied = False
    
    # Get bound_box of object
    boundbox_verts = []
    for i in cut.bound_box:
        boundbox_verts.append(i)
    
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
            
    dim_x = x_max - x_min
    dim_y = y_max - y_min
    dim_z = z_max - z_min
    
    if is_sym:
        dim_x = dim_x*2
    
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
        logger.add_matching_log("{} aspect ratio req : {}".format(pad_msg(div_id), req_aspects))
        logger.add_matching_log("{} aspect ratio 1/2/3 : {} / {} / {}".format(pad_msg(div_id), configure_1, configure_2, configure_3))
    
    # The smallest percentage difference possible
    pds = {arith.percentage_discrepancy(configure_1[0], req_aspects[0]) + arith.percentage_discrepancy(configure_1[1], req_aspects[1]),\
           arith.percentage_discrepancy(configure_1[1], req_aspects[0]) + arith.percentage_discrepancy(configure_1[0], req_aspects[1]),\
           arith.percentage_discrepancy(configure_2[0], req_aspects[0]) + arith.percentage_discrepancy(configure_2[1], req_aspects[1]),\
           arith.percentage_discrepancy(configure_2[1], req_aspects[0]) + arith.percentage_discrepancy(configure_2[0], req_aspects[1]),\
           arith.percentage_discrepancy(configure_3[0], req_aspects[0]) + arith.percentage_discrepancy(configure_3[1], req_aspects[1]),\
           arith.percentage_discrepancy(configure_3[1], req_aspects[0]) + arith.percentage_discrepancy(configure_3[0], req_aspects[1])}
    pd = min(pds)
    cut['pd'] = pd
    
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
            logger.add_matching_log("{} rejected".format(pad_msg(div_id)))
            logger.add_matching_log("")
        return False
    
    if DEBUG_MATCHING:
        logger.add_matching_log("{} accepted".format(pad_msg(div_id)))
        logger.add_matching_log("")
        
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
Remove all potential cuts with pd = -1 (not a volume fit)
Remove all temporary cuts
Flush all associated meshes
"""

def tier_end_cleanup():
    objects = bpy.data.objects
        
    # Remove all potential cuts without acceptable volume
    mesh_to_remove = []
    for obj in objects:
        obj.select = False
        if "potential" in obj.name:
            if obj['pd'] == None:
                logger.add_error_log("!!!!!!!!!!!!")
                logger.add_error_log(str.format("Unexpected error, {} does not have pd",obj.name))
                logger.add_error_log("!!!!!!!!!!!!")
            elif obj['pd'] == -1:
                mesh_to_remove.append(obj.name)
                obj.select = True
        if "temp" in obj.name:
            mesh_to_remove.append(obj.name)
            obj.select = True
            
    bpy.ops.object.delete()
    for mesh in bpy.data.meshes:
        if mesh.name in mesh_to_remove:
            bpy.data.meshes.remove(mesh)


def perform_best_cut(obj):
    objects = bpy.data.objects
    
    # Find the best cut
    best_cut = None
    best_pd = 0
    for cut in objects:
        cut.select = False
        if "cut" in cut.name:
            if best_cut == None:
                best_cut = cut
                best_pd = cut["pd"]
            elif best_pd > cut["pd"]:
                best_cut = cut
                best_pd = cut["pd"]
                
    # Handle symmetric case
    best_name = best_cut.name
    if "neg" in best_name or "pos" in best_name:
        best_name = best_name[0:-4]
    
    pending_cuts = []
    mesh_to_remove = []
    for cut in objects:
        cut.select = False
        if "cut" in cut.name:
            if best_name in cut.name:
                pending_cuts.append(cut)
            else:
                mesh_to_remove.append(cut.name)
                cut.select = True
            
    bpy.ops.object.delete()
    for mesh in bpy.data.meshes:
        if mesh.name in mesh_to_remove:
            bpy.data.meshes.remove(mesh)
    
    for cut in pending_cuts:
        x_max = cut["cut_box"]["x_max"]
        x_min = cut["cut_box"]["x_min"]
        y_max = cut["cut_box"]["y_max"]
        y_min = cut["cut_box"]["y_min"]
        z_max = cut["cut_box"]["z_max"]
        z_min = cut["cut_box"]["z_min"]
        assist = create_cuboid(generate_cuboid_verts(x_max,x_min,y_max,y_min,z_max,z_min),"assist")
        div_level = tier_1_subdivision_level
        i = cut.name.count("_")
        if i>= 4:
            div_level = tier_3_subdivision_level
        elif i == 3:
            div_level = tier_2_subdivision_level
        else:
            div_level = tier_1_subdivision_level
        perform_boolean_difference(assist,obj,div_level)
        
    intermediate_cleanup()
    
def perform_picky_cut(obj,pick_range):
    objects = bpy.data.objects
    
    # Find the cuts in range
    candidates = []
    for cut in objects:
        cut.select = False
        if "cut" in cut.name:
            if math.floor(cut["pd"]*100) in pick_range:
                candidates.append(cut)
    
    chosen_cut = None
    if len(candidates) >= 1:
        pick_id = random.randint(0,len(candidates)-1)
        chosen_cut =candidates[pick_id]
    else:
        perform_best_cut(obj)
        return
    
    # Handle symmetric case
    chosen_name = chosen_cut.name
    if "neg" in chosen_name or "pos" in chosen_name:
        chosen_name = chosen_name[0:-4]
    
    pending_cuts = []
    mesh_to_remove = []
    for cut in objects:
        cut.select = False
        if "cut" in cut.name:
            if chosen_name in cut.name:
                pending_cuts.append(cut)
            else:
                mesh_to_remove.append(cut.name)
                cut.select = True
            
    bpy.ops.object.delete()
    for mesh in bpy.data.meshes:
        if mesh.name in mesh_to_remove:
            bpy.data.meshes.remove(mesh)
    
    for cut in pending_cuts:
        x_max = cut["cut_box"]["x_max"]
        x_min = cut["cut_box"]["x_min"]
        y_max = cut["cut_box"]["y_max"]
        y_min = cut["cut_box"]["y_min"]
        z_max = cut["cut_box"]["z_max"]
        z_min = cut["cut_box"]["z_min"]
        assist = create_cuboid(generate_cuboid_verts(x_max,x_min,y_max,y_min,z_max,z_min),"assist")
        div_level = tier_1_subdivision_level
        i = cut.name.count("_")
        if i>= 4:
            div_level = tier_3_subdivision_level
        elif i == 3:
            div_level = tier_2_subdivision_level
        else:
            div_level = tier_1_subdivision_level
        perform_boolean_difference(assist,obj,div_level)
        
    intermediate_cleanup()

def rename_cuts(name):
    objects = bpy.data.objects
    for cut in objects:
        if "cut" in cut.name:
            if "pos" in cut.name:
                new_name = str.format("{}_pos", name)
                logger.add_choice_log(str.format("{} is chosen as {}",cut.name,new_name))
                cut.name = new_name
                cut.data.name = new_name
            elif "neg" in cut.name:
                new_name = str.format("{}_neg", name)
                logger.add_choice_log(str.format("{} is chosen as {}",cut.name,new_name))
                cut.name = new_name
                cut.data.name = new_name
            else:
                logger.add_choice_log(str.format("{} is chosen as {}",cut.name,name))
                cut.name = name
                cut.data.name = name
    logger.add_choice_log("")
    
def autocut_main(cut_reqs,picks):
    logger.log_start()
    volume = 1.0
    i = 0
    obj = bpy.context.active_object
    
    for cut_req in cut_reqs:
        req_volume_ratio = cut_req["volume"]/volume
        req_aspect_ratio = cut_req["aspect"]
        req_aspects = []
        req_aspects.append(req_aspect_ratio[0]/req_aspect_ratio[1])
        req_aspects.append(req_aspect_ratio[2]/req_aspect_ratio[1])
        
        tier_1_matching(obj, req_volume_ratio, req_aspects)
        if picks[i] == 0:
            perform_best_cut(obj)
        elif picks[i] == 1:
            perform_picky_cut(obj,range(math.floor(allowed_pd_aspect*100),math.floor(mediocre_pd_cap*100)))
        else:
            perform_picky_cut(obj,range(math.floor(mediocre_pd_cap*100),math.floor(bad_pd_cap*100)))
            
        rename_cuts(str.format("component_{}", i+1))
        
        # TODO: use actual volume instead of req
        volume = volume-req_volume_ratio
        i += 1
    
    logger.log_exit()
    
"""
Perform only one cutting without separation for debugging purpose
"""
def autocut_debug_main(cut_req):
    logger.log_start()
    obj = bpy.context.active_object
    
    req_volume_ratio = cut_req["volume"]
    req_aspect_ratio = cut_req["aspect"]
    req_aspects = []
    req_aspects.append(req_aspect_ratio[0]/req_aspect_ratio[1])
    req_aspects.append(req_aspect_ratio[2]/req_aspect_ratio[1])
    
    tier_1_matching(obj, req_volume_ratio, req_aspects)
    
    logger.log_exit()
    
def tier_1_matching(obj, req_volume_ratio, req_aspects):
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
    y_max_box = y_max + y_interval
    y_min_box = y_min - y_interval

    this_y = y_min
    obj.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,tier_1_divs):  
        y_near = this_y
        this_y = this_y + y_interval
        y_far = this_y
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_far,y_min_box,z_max_box,z_min_box),name)
        elif i ++ tier_1_divs - 1:
            cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_near,z_max_box,z_min_box),name)
        else:  
            cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_far,y_near,z_max_box,z_min_box),name)
        
        perform_boolean_intersection(obj,cuboid,tier_1_subdivision_level)
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
        logger.add_matching_log("**************** Tier 1 matching starts")
        logger.add_matching_log("")
    # Find a cut with volume just bigger than required volume
    y_near = y_min
    y_far = y_near
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in range(0,tier_1_divs-1):
        div_id = str.format("{}", cut_id)
        accumulated_volume_ratio += volume_ratios[i]
        y_far = y_near + (i+1)*y_interval
        if accumulated_volume_ratio > req_volume_ratio or arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= allowed_pd_volume:
            name = str.format("temp_cut_{}", cut_id)
            tier_1_cut = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_far,y_min_box,z_max_box,z_min_box),name)
            tier_1_cut["cut_box"] = {"x_max":x_max_box,"x_min":x_min_box\
                                     ,"y_max":y_far,"y_min":y_min_box\
                                     ,"z_max":z_max_box,"z_min":z_min_box}
            perform_boolean_intersection(obj,tier_1_cut,tier_1_subdivision_level)
            is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_1_cut,False)
            if is_accepted_cut:
                tier_1_cut.name = str.format("accepted_cut_{}", cut_id)
                tier_1_cut.data.name = str.format("accepted_cut_{}", cut_id)
            elif accumulated_volume_ratio > req_volume_ratio:
                tier_1_cut.name = str.format("potential_cut_{}", cut_id)
                tier_1_cut.data.name = str.format("potential_cut_{}", cut_id)
                tier_2_matching_sym(cut_id, tier_1_cut, req_volume_ratio/accumulated_volume_ratio, req_aspects)
        cut_id += 1
        
    #tier_end_cleanup()
           
    if DEBUG_MATCHING:     
        logger.add_matching_log("**************** Tier 1 matching ends")
        logger.add_matching_log("")
    
def tier_2_matching_sym(tier_1_id, tier_1_cut, req_volume_ratio, req_aspects):
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
    x_max_box = x_max + x_interval
    x_min_box = x_min - x_interval

    this_x = x_min
    tier_1_cut.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,tier_2_divs):  
        x_near = this_x
        this_x = this_x + x_interval
        x_far = this_x
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = create_cuboid(generate_cuboid_verts(x_far,x_min_box,y_max_box,y_min_box,z_max_box,z_min_box),name)
        elif i == tier_2_divs -1:
            cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
        else:
            cuboid = create_cuboid(generate_cuboid_verts(x_far,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
        
        perform_boolean_intersection(tier_1_cut,cuboid,tier_2_subdivision_level)
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
        logger.add_matching_log("******** Tier 2 sym matching of div {}".format(tier_1_id))
        logger.add_matching_log("")
        
    # Find a cut with volume just bigger than required volume (symmetric case)
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in range(0,math.floor((tier_2_divs+1)/2)-1):  
        accumulated_volume_ratio += volume_ratios[i]
        accumulated_volume_ratio += volume_ratios[tier_2_divs-1-i]
        div_id = str.format("{}_{}", tier_1_id, cut_id)
        x_near = x_min + (i+1)*x_interval
        x_far = x_max - (i+1)*x_interval
        x_dim = (x_max-x_min)-(x_far-x_near)
        
        if accumulated_volume_ratio > req_volume_ratio or arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= allowed_pd_volume:
            name = str.format("temp_cut_{}", div_id)
            pos_name = str.format("{}_pos",name)
            neg_name = str.format("{}_neg",name)
            tier_2_cut_pos = create_cuboid(generate_cuboid_verts(x_max_box,x_far,y_max_box,y_min_box,z_max_box,z_min_box),pos_name)
            tier_2_cut_pos["cut_box"] = {"x_max":x_max_box,"x_min":x_far\
                                         ,"y_max":tier_1_cut["cut_box"]["y_max"],"y_min":tier_1_cut["cut_box"]["y_min"]\
                                         ,"z_max":z_max_box,"z_min":z_min_box}
            tier_2_cut_neg = create_cuboid(generate_cuboid_verts(x_near,x_min_box,y_max_box,y_min_box,z_max_box,z_min_box),neg_name)
            tier_2_cut_neg["cut_box"] = {"x_max":x_near,"x_min":x_min_box\
                                         ,"y_max":tier_1_cut["cut_box"]["y_max"],"y_min":tier_1_cut["cut_box"]["y_min"]\
                                         ,"z_max":z_max_box,"z_min":z_min_box}
            perform_boolean_intersection(tier_1_cut,tier_2_cut_pos,tier_2_subdivision_level)
            perform_boolean_intersection(tier_1_cut,tier_2_cut_neg,tier_2_subdivision_level)
            is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_2_cut_pos,True)
            tier_2_cut_neg['pd'] =tier_2_cut_pos['pd']
            if is_accepted_cut:
                tier_2_cut_pos.name = str.format("accepted_cut_{}_pos", div_id)
                tier_2_cut_pos.data.name = str.format("accepted_cut_{}_pos", div_id)
                tier_2_cut_neg.name = str.format("accepted_cut_{}_neg", div_id)
                tier_2_cut_neg.data.name = str.format("accepted_cut_{}_neg", div_id)
            elif accumulated_volume_ratio > req_volume_ratio:
                tier_2_cut_pos.name = str.format("potential_cut_{}_pos", div_id)
                tier_2_cut_pos.data.name = str.format("potential_cut_{}_pos", div_id)
                tier_2_cut_neg.name = str.format("potential_cut_{}_neg", div_id)
                tier_2_cut_neg.data.name = str.format("potential_cut_{}_neg", div_id)
                tier_3_matching(tier_1_id, cut_id, [tier_2_cut_pos, tier_2_cut_neg], req_volume_ratio/accumulated_volume_ratio, req_aspects, x_dim)
        cut_id += 1
        
    tier_end_cleanup()
                
    if DEBUG_MATCHING:     
        logger.add_matching_log("******** Tier 2 sym matching of div {} ends".format(tier_1_id))
        logger.add_matching_log("")

def tier_2_matching_asym(tier_1_id, tier_1_cut, req_volume_ratio, req_aspects):
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
    x_max_box = x_max + x_interval
    x_min_box = x_min - x_interval

    this_x = x_min
    tier_1_cut.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,tier_2_divs):  
        x_near = this_x
        this_x = this_x + x_interval
        x_far = this_x
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = create_cuboid(generate_cuboid_verts(x_far,x_min_box,y_max_box,y_min_box,z_max_box,z_min_box),name)
        elif i == tier_2_divs -1:
            cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
        else:
            cuboid = create_cuboid(generate_cuboid_verts(x_far,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
        
        perform_boolean_intersection(tier_1_cut,cuboid,tier_2_subdivision_level)
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
        logger.add_matching_log("******** Tier 2 asym matching of div {}".format(tier_1_id))
        logger.add_matching_log("")
        
    # Find a cut with volume just bigger than required volume (symmetric case)
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in reversed(range(1,math.floor((tier_2_divs+1)/2))): 
        # Odd number of divisions, first volume is the one piece in the center
        if tier_2_divs%2 == 1 and i == math.floor((tier_2_divs+1)/2)-1:
            accumulated_volume_ratio += volume_ratios[i]
        # Otherwise add the 2 pieces in the center
        else:
            accumulated_volume_ratio += volume_ratios[i]
            accumulated_volume_ratio += volume_ratios[tier_2_divs-1-i]
        
        div_id = str.format("{}_{}", tier_1_id, cut_id)
        x_near = x_min + i*x_interval
        x_far = x_max - i*x_interval
        x_dim = x_far-x_near
        
        if accumulated_volume_ratio > req_volume_ratio or arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= allowed_pd_volume:
            name = str.format("temp_cut_{}", div_id)
            tier_2_cut = create_cuboid(generate_cuboid_verts(x_far,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
            tier_2_cut["cut_box"] = {"x_max":x_far,"x_min":x_near\
                                     ,"y_max":tier_1_cut["cut_box"]["y_max"],"y_min":tier_1_cut["cut_box"]["y_min"]\
                                     ,"z_max":z_max_box,"z_min":z_min_box}
            perform_boolean_intersection(tier_1_cut,tier_2_cut,tier_2_subdivision_level)
            is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_2_cut,False)
            if is_accepted_cut:
                tier_2_cut.name = str.format("accepted_cut_{}", div_id)
                tier_2_cut.data.name = str.format("accepted_cut_{}", div_id)
            elif accumulated_volume_ratio > req_volume_ratio:
                tier_2_cut.name = str.format("potential_cut_{}", div_id)
                tier_2_cut.data.name = str.format("potential_cut_{}", div_id)
                tier_3_matching(tier_1_id, cut_id, [tier_2_cut], req_volume_ratio/accumulated_volume_ratio, req_aspects, x_dim)
        cut_id += 1
        
    tier_end_cleanup()
                
    if DEBUG_MATCHING:     
        logger.add_matching_log("******** Tier 2 asym matching of div {} ends".format(tier_1_id))
        logger.add_matching_log("")

"""
tier_2_cuts is a list containing [pos_cut, neg_cut] or one cut only
"""
def tier_3_matching(tier_1_id, tier_2_id, tier_2_cuts, req_volume_ratio, req_aspects, x_dim):
    # Get bound_box of object
    boundbox_verts = []
    for tier_2_cut in tier_2_cuts:
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
    z_max_box = z_max + z_interval
    z_min_box = z_min - z_interval

    this_z = z_min
    for tier_2_cut in tier_2_cuts:
        tier_2_cut.select = False
    
    if len(tier_2_cuts) < 1:
        logger.add_error_log(str.format("Error at tier 3 cut for {}, no param passed in."))
        return
    divisions = []
    cutsurface_areas = []
    for i in range(0,tier_3_divs):  
        z_near = this_z
        this_z = this_z + z_interval
        z_far = this_z
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_min_box),name)
        elif i == tier_3_divs - 1:
            cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_max_box,z_near),name)
        else:
            cuboid = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_near),name)
        
        perform_boolean_intersection(tier_2_cuts[0],cuboid,tier_3_subdivision_level)
       
        divisions.append(cuboid)
                    
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"z",z_near,z_far,z_interval))
        
    volume_ratios = get_volume_ratios(cutsurface_areas)
    
    #print("tier 3 volume_ratios")
    #print(volume_ratios)
    #print("tier 3 cutsurface_areas")
    #print(cutsurface_areas)
    
    analysis.analyse_volume_approximation(tier_2_cuts[0], divisions, volume_ratios)
    
    intermediate_cleanup()
    
    if DEBUG_MATCHING:
        logger.add_matching_log("Tier 3 matching of div {}_{}".format(tier_1_id, tier_2_id))
        logger.add_matching_log("")
    
    # Find acceptable cut
    z_near = z_min
    z_far = z_near
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in range(0,tier_3_divs-1):  
        accumulated_volume_ratio += volume_ratios[i]   
        div_id = str.format("{}_{}_{}",tier_1_id,tier_2_id,cut_id) 
        z_far = z_near + (i+1)*z_interval 
        
        if arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= allowed_pd_volume:
            name = str.format("temp_cut_{}", div_id)
            if len(tier_2_cuts) == 2:
                pos_name = str.format("{}_pos",name)
                neg_name = str.format("{}_neg",name)
                x_center = (x_max_box + x_min_box)/2
                tier_3_cut_pos = create_cuboid(generate_cuboid_verts(x_max_box,x_center,y_max_box,y_min_box,z_far,z_min_box),pos_name)
                tier_3_cut_pos["cut_box"] = {"x_max":tier_2_cuts[0]["cut_box"]["x_max"],"x_min":tier_2_cuts[0]["cut_box"]["x_min"]\
                                             ,"y_max":tier_2_cuts[0]["cut_box"]["y_max"],"y_min":tier_2_cuts[0]["cut_box"]["y_min"]\
                                             ,"z_max":z_far,"z_min":z_min_box}
                tier_3_cut_neg = create_cuboid(generate_cuboid_verts(x_center,x_min_box,y_max_box,y_min_box,z_far,z_min_box),neg_name)
                tier_3_cut_neg["cut_box"] = {"x_max":tier_2_cuts[1]["cut_box"]["x_max"],"x_min":tier_2_cuts[1]["cut_box"]["x_min"]\
                                             ,"y_max":tier_2_cuts[1]["cut_box"]["y_max"],"y_min":tier_2_cuts[1]["cut_box"]["y_min"]\
                                             ,"z_max":z_far,"z_min":z_min_box}
                perform_boolean_intersection(tier_2_cuts[0],tier_3_cut_pos,tier_3_subdivision_level)
                perform_boolean_intersection(tier_2_cuts[1],tier_3_cut_neg,tier_3_subdivision_level)
                is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_3_cut_pos,True)
                tier_3_cut_neg['pd'] =tier_3_cut_pos['pd']
                if is_accepted_cut:
                    tier_3_cut_pos.name = str.format("accepted_cut_{}_pos", div_id)
                    tier_3_cut_pos.data.name = str.format("accepted_cut_{}_pos", div_id)
                    tier_3_cut_neg.name = str.format("accepted_cut_{}_neg", div_id)
                    tier_3_cut_neg.data.name = str.format("accepted_cut_{}_neg", div_id)
                else:
                    tier_3_cut_pos.name = str.format("potential_cut_{}_pos", div_id)
                    tier_3_cut_pos.data.name = str.format("potential_cut_{}_pos", div_id)
                    tier_3_cut_neg.name = str.format("potential_cut_{}_neg", div_id)
                    tier_3_cut_neg.data.name = str.format("potential_cut_{}_neg", div_id)
            elif len(tier_2_cuts) == 1:
                tier_3_cut = create_cuboid(generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_min_box),name)
                tier_3_cut["cut_box"] = {"x_max":tier_2_cuts[0]["cut_box"]["x_max"],"x_min":tier_2_cuts[0]["cut_box"]["x_min"]\
                                         ,"y_max":tier_2_cuts[0]["cut_box"]["y_max"],"y_min":tier_2_cuts[0]["cut_box"]["y_min"]\
                                         ,"z_max":z_far,"z_min":z_min_box}
                perform_boolean_intersection(tier_2_cuts[0],tier_3_cut,tier_3_subdivision_level)
                is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_3_cut,False)
                if is_accepted_cut:
                    tier_3_cut.name = str.format("accepted_cut_{}", div_id)
                    tier_3_cut.data.name = str.format("accepted_cut_{}", div_id)
                else:
                    tier_3_cut.name = str.format("potential_cut_{}", div_id)
                    tier_3_cut.data.name = str.format("potential_cut_{}", div_id)
            else:
                logger.add_error_log(str.format("Invalid parameter to tier_3_cut for {}",tier_2_id))
        cut_id += 1
                
    if DEBUG_MATCHING:     
        logger.add_matching_log("Tier 3 matching of div {}_{} ends".format(tier_1_id, tier_2_id))
        logger.add_matching_log("")

            
            
            
            
            
            