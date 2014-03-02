'''
@author: Jiang HaoYuan, National University of Singapore
'''

import bpy
import bmesh

import math
import arithmetic_helper as arith
import analytic_helper as analysis
import blender_ops_helper as bops
import transformer_config as config

from TransformerLogger import TransformerLogger

# Logger
logger = TransformerLogger()

"""
Get a bunch of values from the boundbox of an object
"""
def process_boundbox(boundboxes,num_divs):
    boundbox_verts = []
    for boundbox in boundboxes:
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
    
    x_interval = (x_max-x_min)/num_divs
    y_interval = (y_max-y_min)/num_divs
    z_interval = (z_max-z_min)/num_divs
    x_max_box = x_max + x_interval
    x_min_box = x_min - x_interval
    y_max_box = y_max + y_interval
    y_min_box = y_min - y_interval
    z_max_box = z_max + z_interval
    z_min_box = z_min - z_interval
    
    params = {"x_min":x_min,"x_max":x_max,"y_min":y_min,"y_max":y_max,"z_min":z_min,"z_max":z_max,\
            "x_interval":x_interval,"y_interval":y_interval,"z_interval":z_interval,\
            "x_max_box":x_max_box,"x_min_box":x_min_box,"y_max_box":y_max_box,"y_min_box":y_min_box,"z_max_box":z_max_box,"z_min_box":z_min_box}
    return params
     
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
        if math.fabs(face.normal[dim]-1)<= config.normal_tolerance:
            average_plane = 0
            for vert in face.vertices:
                average_plane += vertices[vert].co[dim]
            average_plane = average_plane/len(face.vertices)
            if average_plane >= far_threshold:
                area = area+face.area*(average_plane-near_plane)/interval
        # Facing towards negative axis
        elif math.fabs(face.normal[dim]+1) <= config.normal_tolerance:
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
def get_volume_ratios(cut_id, cut_surface_areas):
    volume_ratios = []
    area_sum = math.fsum(cut_surface_areas)
    if area_sum == 0:
        logger.add_error_log(str.format("Error at cut {} produced area sum 0",cut_id))
    for area in cut_surface_areas:
        volume_ratios.append(area/area_sum)
    return volume_ratios

"""
Pad the print message in verify cut with appropriate number of '*'
"""
def pad_msg(div_id):
    if div_id.count('_') == 0:
        return ""
    elif div_id.count('_') == 1:
        return "**********"
    else:
        return "********************"
        
"""
Verify if a cut can be accepted based on its volume ratio and aspect ratio
temp_sto is a dictionary containing some values to be written back to the cut
Return BOOLEAN
"""
def verify_cut(div_id, req_volume_ratio, req_aspects, estimated_volume, cut):
    # Matching volume 
    if config.DEBUG_MATCHING:
        logger.add_matching_log("{} matching {}".format(pad_msg(div_id), div_id))
        logger.add_matching_log("{} volume req/act : {} / {}".format(pad_msg(div_id), req_volume_ratio, estimated_volume))

    if not arith.percentage_discrepancy(estimated_volume, req_volume_ratio) <= config.allowed_pd_volume:
        if config.DEBUG_MATCHING:
            logger.add_matching_log("{} rejected".format(pad_msg(div_id)))
            logger.add_matching_log("")
        cut['pd'] = -1
        return False
    
    # Matching aspect ratio    
    aspect_ratio_satisfied = False
    
    params = process_boundbox([cut.bound_box],1)
    x_max = params["x_max"]
    x_min = params["x_min"]
    y_max = params["y_max"]
    y_min = params["y_min"]
    z_max = params["z_max"]
    z_min = params["z_min"]
            
    dim_x = x_max - x_min
    dim_y = y_max - y_min
    dim_z = z_max - z_min
    
    configure_1 = []
    configure_1.append(dim_x/dim_y)
    configure_1.append(dim_z/dim_y)
    configure_2 = []
    configure_2.append(dim_y/dim_x)
    configure_2.append(dim_z/dim_x)
    configure_3 = []
    configure_3.append(dim_x/dim_z)
    configure_3.append(dim_y/dim_z)
    
    if config.DEBUG_MATCHING:
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
    
    if (arith.percentage_discrepancy(configure_1[0], req_aspects[0]) <= config.allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_1[1], req_aspects[1]) <= config.allowed_pd_aspect) \
    or (arith.percentage_discrepancy(configure_1[1], req_aspects[0]) <= config.allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_1[0], req_aspects[1]) <= config.allowed_pd_aspect):
        aspect_ratio_satisfied = True
    
    if (arith.percentage_discrepancy(configure_2[0], req_aspects[0]) <= config.allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_2[1], req_aspects[1]) <= config.allowed_pd_aspect) \
    or (arith.percentage_discrepancy(configure_2[1], req_aspects[0]) <= config.allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_2[0], req_aspects[1]) <= config.allowed_pd_aspect):
        aspect_ratio_satisfied = True
        
    if (arith.percentage_discrepancy(configure_3[0], req_aspects[0]) <= config.allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_3[1], req_aspects[1]) <= config.allowed_pd_aspect) \
    or (arith.percentage_discrepancy(configure_3[1], req_aspects[0]) <= config.allowed_pd_aspect \
    and arith.percentage_discrepancy(configure_3[0], req_aspects[1]) <= config.allowed_pd_aspect):
        aspect_ratio_satisfied = True
    
    if not aspect_ratio_satisfied:
        if config.DEBUG_MATCHING:
            logger.add_matching_log("{} rejected".format(pad_msg(div_id)))
            logger.add_matching_log("")
        return False
    
    if config.DEBUG_MATCHING:
        logger.add_matching_log("{} accepted".format(pad_msg(div_id)))
        logger.add_matching_log("")
        
    return True
            
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
            
def cutting_start(obj,req_volume_ratio,req_aspects,is_sym):
    if is_sym:
        sym_tier_1_matching(obj, req_volume_ratio, req_aspects)
    else:
        asym_tier_1_matching(obj, req_volume_ratio, req_aspects)

"""
Asym cuttings
"""
def asym_tier_1_matching(obj, req_volume_ratio, req_aspects):
    params = process_boundbox([obj.bound_box],config.tier_1_divs)
    y_min = params["y_min"]
    y_interval = params["y_interval"]
    x_max_box = params["x_max_box"]
    x_min_box = params["x_min_box"]
    y_max_box = params["y_max_box"]
    y_min_box = params["y_min_box"]
    z_max_box = params["z_max_box"]
    z_min_box = params["z_min_box"]
    
    this_y = y_min
    obj.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,config.tier_1_divs):  
        y_near = this_y
        this_y = this_y + y_interval
        y_far = this_y
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_far,y_min_box,z_max_box,z_min_box),name)
        elif i == config.tier_1_divs - 1:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_near,z_max_box,z_min_box),name)
        else:  
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_far,y_near,z_max_box,z_min_box),name)
        
        bops.perform_boolean_intersection(obj,cuboid,config.tier_1_subdivision_level)
        divisions.append(cuboid)
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"y",y_near,y_far,y_interval))
    
    volume_ratios = get_volume_ratios("tier_1",cutsurface_areas)
    
    analysis.analyse_volume_approximation(obj, divisions, volume_ratios, logger)
    
    intermediate_cleanup()
    
    if config.DEBUG_MATCHING:
        logger.add_matching_log("Asym tier 1 matching starts")
        logger.add_matching_log("")
    # Find a cut with volume just bigger than required volume
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in range(0,config.tier_1_divs-1):
        div_id = str.format("{}", cut_id)
        accumulated_volume_ratio += volume_ratios[i]
        y_far = y_min + (i+1)*y_interval
        if accumulated_volume_ratio > req_volume_ratio or arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= config.allowed_pd_volume:
            name = str.format("temp_cut_{}", cut_id)
            tier_1_cut = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_far,y_min_box,z_max_box,z_min_box),name)
            tier_1_cut["cut_box"] = {"x_max":x_max_box,"x_min":x_min_box\
                                     ,"y_max":y_far,"y_min":y_min_box\
                                     ,"z_max":z_max_box,"z_min":z_min_box}
            bops.perform_boolean_intersection(obj,tier_1_cut,config.tier_1_subdivision_level)
            is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_1_cut)
            if is_accepted_cut:
                tier_1_cut.name = str.format("accepted_cut_{}", cut_id)
                tier_1_cut.data.name = str.format("accepted_cut_{}", cut_id)
            elif accumulated_volume_ratio > req_volume_ratio:
                tier_1_cut.name = str.format("potential_cut_{}", cut_id)
                tier_1_cut.data.name = str.format("potential_cut_{}", cut_id)
                asym_tier_2_matching(cut_id, tier_1_cut, req_volume_ratio/accumulated_volume_ratio, req_aspects)
        cut_id += 1
        
    tier_end_cleanup()
           
    if config.DEBUG_MATCHING:     
        logger.add_matching_log("Asym tier 1 matching ends")
        logger.add_matching_log("")
        
def asym_tier_2_matching(tier_1_id, tier_1_cut, req_volume_ratio, req_aspects):
    params = process_boundbox([tier_1_cut.bound_box],config.tier_2_divs)
    x_min = params["x_min"]
    x_max = params["x_max"]
    x_interval = params["x_interval"]
    x_max_box = params["x_max_box"]
    x_min_box = params["x_min_box"]
    y_max_box = params["y_max_box"]
    y_min_box = params["y_min_box"]
    z_max_box = params["z_max_box"]
    z_min_box = params["z_min_box"]

    this_x = x_min
    tier_1_cut.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,config.tier_2_divs):  
        x_near = this_x
        this_x = this_x + x_interval
        x_far = this_x
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_far,x_min_box,y_max_box,y_min_box,z_max_box,z_min_box),name)
        elif i == config.tier_2_divs -1:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
        else:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_far,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
        
        bops.perform_boolean_intersection(tier_1_cut,cuboid,config.tier_2_subdivision_level)
        divisions.append(cuboid)
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"x",x_near,x_far,x_interval))
        
    volume_ratios = get_volume_ratios(tier_1_id,cutsurface_areas)
    
    analysis.analyse_volume_approximation(tier_1_cut, divisions, volume_ratios, logger)
    
    intermediate_cleanup()
    
    if config.DEBUG_MATCHING:
        logger.add_matching_log("********** Asym Tier 2 matching of div {}".format(tier_1_id))
        logger.add_matching_log("")
        
    # Find a cut with volume just bigger than required volume (symmetric case)
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in reversed(range(1,math.floor((config.tier_2_divs+1)/2))): 
        # Odd number of divisions, first volume is the one piece in the center
        if config.tier_2_divs%2 == 1 and i == math.floor((config.tier_2_divs+1)/2)-1:
            accumulated_volume_ratio += volume_ratios[i]
        # Otherwise add the 2 pieces in the center
        else:
            accumulated_volume_ratio += volume_ratios[i]
            accumulated_volume_ratio += volume_ratios[config.tier_2_divs-1-i]
        
        div_id = str.format("{}_{}", tier_1_id, cut_id)
        x_near = x_min + i*x_interval
        x_far = x_max - i*x_interval
        
        if accumulated_volume_ratio > req_volume_ratio or arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= config.allowed_pd_volume:
            name = str.format("temp_cut_{}", div_id)
            tier_2_cut = bops.create_cuboid(bops.generate_cuboid_verts(x_far,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
            tier_2_cut["cut_box"] = {"x_max":x_far,"x_min":x_near\
                                     ,"y_max":tier_1_cut["cut_box"]["y_max"],"y_min":tier_1_cut["cut_box"]["y_min"]\
                                     ,"z_max":z_max_box,"z_min":z_min_box}
            bops.perform_boolean_intersection(tier_1_cut,tier_2_cut,config.tier_2_subdivision_level)
            is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_2_cut)
            if is_accepted_cut:
                tier_2_cut.name = str.format("accepted_cut_{}", div_id)
                tier_2_cut.data.name = str.format("accepted_cut_{}", div_id)
            elif accumulated_volume_ratio > req_volume_ratio:
                tier_2_cut.name = str.format("potential_cut_{}", div_id)
                tier_2_cut.data.name = str.format("potential_cut_{}", div_id)
                asym_tier_3_matching(tier_1_id, cut_id, tier_2_cut, req_volume_ratio/accumulated_volume_ratio, req_aspects)
        cut_id += 1
        
    tier_end_cleanup()
                
    if config.DEBUG_MATCHING:     
        logger.add_matching_log("********** Asym tier 2 matching of div {} ends".format(tier_1_id))
        logger.add_matching_log("")
        
def asym_tier_3_matching(tier_1_id, tier_2_id, tier_2_cut, req_volume_ratio, req_aspects):
    boundboxes = []
    boundboxes.append(tier_2_cut.bound_box)
    params = process_boundbox(boundboxes,config.tier_3_divs)
    z_min = params["z_min"]
    z_interval = params["z_interval"]
    x_max_box = params["x_max_box"]
    x_min_box = params["x_min_box"]
    y_max_box = params["y_max_box"]
    y_min_box = params["y_min_box"]
    z_max_box = params["z_max_box"]
    z_min_box = params["z_min_box"]
    
    this_z = z_min
    tier_2_cut.select = False
    
    divisions = []
    cutsurface_areas = []
    for i in range(0,config.tier_3_divs):  
        z_near = this_z
        this_z = this_z + z_interval
        z_far = this_z
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_min_box),name)
        elif i == config.tier_3_divs - 1:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_max_box,z_near),name)
        else:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_near),name)
        
        bops.perform_boolean_intersection(tier_2_cut,cuboid,config.tier_3_subdivision_level)
       
        divisions.append(cuboid)
                    
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"z",z_near,z_far,z_interval))
        
    volume_ratios = get_volume_ratios(str.format("{}_{}",tier_1_id,tier_2_id),cutsurface_areas)
    
    analysis.analyse_volume_approximation(tier_2_cut, divisions, volume_ratios, logger)
    
    intermediate_cleanup()
    
    if config.DEBUG_MATCHING:
        logger.add_matching_log("******************** Asym tier 3 matching of div {}_{}".format(tier_1_id, tier_2_id))
        logger.add_matching_log("")
    
    # Find acceptable cut
    z_near = z_min
    z_far = z_near
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in range(0,config.tier_3_divs-1):  
        accumulated_volume_ratio += volume_ratios[i]   
        div_id = str.format("{}_{}_{}",tier_1_id,tier_2_id,cut_id) 
        z_far = z_near + (i+1)*z_interval 
        
        if arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= config.allowed_pd_volume:
            name = str.format("temp_cut_{}", div_id)
            tier_3_cut = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_min_box),name)
            tier_3_cut["cut_box"] = {"x_max":tier_2_cut["cut_box"]["x_max"],"x_min":tier_2_cut["cut_box"]["x_min"]\
                                     ,"y_max":tier_2_cut["cut_box"]["y_max"],"y_min":tier_2_cut["cut_box"]["y_min"]\
                                     ,"z_max":z_far,"z_min":z_min_box}
            bops.perform_boolean_intersection(tier_2_cut,tier_3_cut,config.tier_3_subdivision_level)
            is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_3_cut)
            if is_accepted_cut:
                tier_3_cut.name = str.format("accepted_cut_{}", div_id)
                tier_3_cut.data.name = str.format("accepted_cut_{}", div_id)
            else:
                tier_3_cut.name = str.format("potential_cut_{}", div_id)
                tier_3_cut.data.name = str.format("potential_cut_{}", div_id)
           
        cut_id += 1
                
    if config.DEBUG_MATCHING:     
        logger.add_matching_log("******************** Asym tier 3 matching of div {}_{} ends".format(tier_1_id, tier_2_id))
        logger.add_matching_log("")

"""
Symmetric cuttings
"""
def sym_tier_1_matching(obj, req_volume_ratio, req_aspects):
    params = process_boundbox([obj.bound_box],config.tier_1_divs)
    y_min = params["y_min"]
    y_interval = params["y_interval"]
    x_max_box = params["x_max_box"]
    x_min_box = params["x_min_box"]
    y_max_box = params["y_max_box"]
    y_min_box = params["y_min_box"]
    z_max_box = params["z_max_box"]
    z_min_box = params["z_min_box"]
    
    this_y = y_min
    obj.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,config.tier_1_divs):  
        y_near = this_y
        this_y = this_y + y_interval
        y_far = this_y
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_far,y_min_box,z_max_box,z_min_box),name)
        elif i == config.tier_1_divs - 1:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_near,z_max_box,z_min_box),name)
        else:  
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_far,y_near,z_max_box,z_min_box),name)
        
        bops.perform_boolean_intersection(obj,cuboid,config.tier_1_subdivision_level)
        divisions.append(cuboid)
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"y",y_near,y_far,y_interval))
    
    volume_ratios = get_volume_ratios("tier_1",cutsurface_areas)
    
    analysis.analyse_volume_approximation(obj, divisions, volume_ratios, logger)
    
    intermediate_cleanup()
    
    if config.DEBUG_MATCHING:
        logger.add_matching_log("Symmetric tier 1 matching starts")
        logger.add_matching_log("")
    # Find a cut with volume just bigger than required volume
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in range(0,config.tier_1_divs-1):
        accumulated_volume_ratio += volume_ratios[i]
        y_far = y_min + (i+1)*y_interval
        # twice the required volume ratio is used here since we need to cut 2 parts
        if accumulated_volume_ratio > 2*req_volume_ratio or arith.percentage_discrepancy(accumulated_volume_ratio, 2*req_volume_ratio) <= config.allowed_pd_volume:
            name = str.format("potential_cut_{}", cut_id)
            tier_1_cut = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_far,y_min_box,z_max_box,z_min_box),name)
            tier_1_cut["cut_box"] = {"x_max":x_max_box,"x_min":x_min_box\
                                     ,"y_max":y_far,"y_min":y_min_box\
                                     ,"z_max":z_max_box,"z_min":z_min_box}
            bops.perform_boolean_intersection(obj,tier_1_cut,config.tier_1_subdivision_level)
            tier_1_cut['pd'] = -1
            sym_tier_2_matching(cut_id, tier_1_cut, req_volume_ratio/accumulated_volume_ratio, req_aspects)
        cut_id += 1
        
    tier_end_cleanup()
           
    if config.DEBUG_MATCHING:     
        logger.add_matching_log("Symmetric tier 1 matching ends")
        logger.add_matching_log("")
    
def sym_tier_2_matching(tier_1_id, tier_1_cut, req_volume_ratio, req_aspects):
    params = process_boundbox([tier_1_cut.bound_box],config.tier_2_divs)
    x_min = params["x_min"]
    x_max = params["x_max"]
    x_interval = params["x_interval"]
    x_max_box = params["x_max_box"]
    x_min_box = params["x_min_box"]
    y_max_box = params["y_max_box"]
    y_min_box = params["y_min_box"]
    z_max_box = params["z_max_box"]
    z_min_box = params["z_min_box"]

    this_x = x_min
    tier_1_cut.select = False
    divisions = []
    cutsurface_areas = []
    for i in range(0,config.tier_2_divs):  
        x_near = this_x
        this_x = this_x + x_interval
        x_far = this_x
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_far,x_min_box,y_max_box,y_min_box,z_max_box,z_min_box),name)
        elif i == config.tier_2_divs -1:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
        else:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_far,x_near,y_max_box,y_min_box,z_max_box,z_min_box),name)
        
        bops.perform_boolean_intersection(tier_1_cut,cuboid,config.tier_2_subdivision_level)
        divisions.append(cuboid)
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"x",x_near,x_far,x_interval))
    
    volume_ratios = get_volume_ratios(tier_1_id,cutsurface_areas)
    
    analysis.analyse_volume_approximation(tier_1_cut, divisions, volume_ratios, logger)
    
    intermediate_cleanup()

    if config.DEBUG_MATCHING:
        logger.add_matching_log("********** Tier 2 sym matching of div {}".format(tier_1_id))
        logger.add_matching_log("")
        
    # Find a cut with volume just bigger than required volume (symmetric case)
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in range(0,math.floor((config.tier_2_divs)/2)):  
        accumulated_volume_ratio += volume_ratios[i]
        div_id = str.format("{}_{}", tier_1_id, cut_id)
        x_near = x_min + (i+1)*x_interval
        x_far = x_max - (i+1)*x_interval
        
        if accumulated_volume_ratio > req_volume_ratio or arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= config.allowed_pd_volume:
            name = str.format("temp_cut_{}", div_id)
            pos_name = str.format("{}_pos",name)
            neg_name = str.format("{}_neg",name)
            tier_2_cut_pos = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_far,y_max_box,y_min_box,z_max_box,z_min_box),pos_name)
            tier_2_cut_pos["cut_box"] = {"x_max":x_max_box,"x_min":x_far\
                                         ,"y_max":tier_1_cut["cut_box"]["y_max"],"y_min":tier_1_cut["cut_box"]["y_min"]\
                                         ,"z_max":z_max_box,"z_min":z_min_box}
            tier_2_cut_neg = bops.create_cuboid(bops.generate_cuboid_verts(x_near,x_min_box,y_max_box,y_min_box,z_max_box,z_min_box),neg_name)
            tier_2_cut_neg["cut_box"] = {"x_max":x_near,"x_min":x_min_box\
                                         ,"y_max":tier_1_cut["cut_box"]["y_max"],"y_min":tier_1_cut["cut_box"]["y_min"]\
                                         ,"z_max":z_max_box,"z_min":z_min_box}
            bops.perform_boolean_intersection(tier_1_cut,tier_2_cut_pos,config.tier_2_subdivision_level)
            bops.perform_boolean_intersection(tier_1_cut,tier_2_cut_neg,config.tier_2_subdivision_level)
            is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_2_cut_pos)
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
                sym_tier_3_matching(tier_1_id, cut_id, [tier_2_cut_pos, tier_2_cut_neg], req_volume_ratio/accumulated_volume_ratio, req_aspects)
        cut_id += 1
        
    tier_end_cleanup()
                
    if config.DEBUG_MATCHING:     
        logger.add_matching_log("********** Tier 2 sym matching of div {} ends".format(tier_1_id))
        logger.add_matching_log("")

"""
tier_2_cuts is a list containing [pos_cut, neg_cut] or one cut only
"""
def sym_tier_3_matching(tier_1_id, tier_2_id, tier_2_cuts, req_volume_ratio, req_aspects):
    boundboxes = []
    for tier_2_cut in tier_2_cuts:
        boundboxes.append(tier_2_cut.bound_box)
    params = process_boundbox(boundboxes,config.tier_3_divs)
    z_min = params["z_min"]
    z_interval = params["z_interval"]
    x_interval = params["x_interval"]
    x_max_box = params["x_max_box"]
    x_min_box = params["x_min_box"]
    y_max_box = params["y_max_box"]
    y_min_box = params["y_min_box"]
    z_max_box = params["z_max_box"]
    z_min_box = params["z_min_box"]
    
    this_z = z_min
    for tier_2_cut in tier_2_cuts:
        tier_2_cut.select = False
    
    if len(tier_2_cuts) != 2:
        logger.add_error_log(str.format("Error at symmetric tier 3 cut, should pass in 2 cuts"))
        return
    divisions = []
    cutsurface_areas = []
    for i in range(0,config.tier_3_divs):  
        z_near = this_z
        this_z = this_z + z_interval
        z_far = this_z
        name = str.format("division_{}", i+1)
        cuboid = None
        if i == 0:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_min_box),name)
        elif i == config.tier_3_divs - 1:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_max_box,z_near),name)
        else:
            cuboid = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_min_box,y_max_box,y_min_box,z_far,z_near),name)
        
        bops.perform_boolean_intersection(tier_2_cuts[0],cuboid,config.tier_3_subdivision_level)
       
        divisions.append(cuboid)
                    
        cutsurface_areas.append(get_cut_surfaces_area(cuboid.data.vertices,cuboid.data.polygons,"z",z_near,z_far,z_interval))
        
    volume_ratios = get_volume_ratios(str.format("{}_{}",tier_1_id,tier_2_id),cutsurface_areas)
    
    analysis.analyse_volume_approximation(tier_2_cuts[0], divisions, volume_ratios, logger)
    
    intermediate_cleanup()
    
    if config.DEBUG_MATCHING:
        logger.add_matching_log("******************** Tier 3 matching of div {}_{}".format(tier_1_id, tier_2_id))
        logger.add_matching_log("")
    
    # Find acceptable cut
    z_near = z_min
    z_far = z_near
    accumulated_volume_ratio = 0
    cut_id = 1
    for i in range(0,config.tier_3_divs-1):  
        accumulated_volume_ratio += volume_ratios[i]  
        div_id = str.format("{}_{}_{}",tier_1_id,tier_2_id,cut_id) 
        z_far = z_near + (i+1)*z_interval 
        
        if arith.percentage_discrepancy(accumulated_volume_ratio, req_volume_ratio) <= config.allowed_pd_volume:
            name = str.format("temp_cut_{}", div_id)
            pos_name = str.format("{}_pos",name)
            neg_name = str.format("{}_neg",name)
            x_center = (x_max_box + x_min_box)/2
            x_pos = x_center - x_interval
            x_neg = x_center + x_interval
            tier_3_cut_pos = bops.create_cuboid(bops.generate_cuboid_verts(x_max_box,x_pos,y_max_box,y_min_box,z_far,z_min_box),pos_name)
            tier_3_cut_pos["cut_box"] = {"x_max":tier_2_cuts[0]["cut_box"]["x_max"],"x_min":tier_2_cuts[0]["cut_box"]["x_min"]\
                                         ,"y_max":tier_2_cuts[0]["cut_box"]["y_max"],"y_min":tier_2_cuts[0]["cut_box"]["y_min"]\
                                         ,"z_max":z_far,"z_min":z_min_box}
            tier_3_cut_neg = bops.create_cuboid(bops.generate_cuboid_verts(x_neg,x_min_box,y_max_box,y_min_box,z_far,z_min_box),neg_name)
            tier_3_cut_neg["cut_box"] = {"x_max":tier_2_cuts[1]["cut_box"]["x_max"],"x_min":tier_2_cuts[1]["cut_box"]["x_min"]\
                                         ,"y_max":tier_2_cuts[1]["cut_box"]["y_max"],"y_min":tier_2_cuts[1]["cut_box"]["y_min"]\
                                         ,"z_max":z_far,"z_min":z_min_box}
            bops.perform_boolean_intersection(tier_2_cuts[0],tier_3_cut_pos,config.tier_3_subdivision_level)
            bops.perform_boolean_intersection(tier_2_cuts[1],tier_3_cut_neg,config.tier_3_subdivision_level)
            is_accepted_cut = verify_cut(div_id,req_volume_ratio,req_aspects,accumulated_volume_ratio,tier_3_cut_pos)
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
           
        cut_id += 1
                
    if config.DEBUG_MATCHING:     
        logger.add_matching_log("******************** Tier 3 matching of div {}_{} ends".format(tier_1_id, tier_2_id))
        logger.add_matching_log("")

            
            