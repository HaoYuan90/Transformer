'''
@author: Jiang HaoYuan, National University of Singapore
'''

import bpy
import bmesh

import math
import random
import blender_ops_helper as bops
import transformer_config as config
import transformer_cutting as cutter

from TransformerLogger import TransformerLogger

# Logger
logger = TransformerLogger()

"""
Remove all objects created
and flush all associated meshes
"""
def cut_cleanup(): 
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
    
    perform_specific_cut(obj,best_cut.name)
    
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
    
    perform_specific_cut(obj,chosen_cut.name)
    
"""
Do specific cut with input name
"""
def perform_specific_cut(obj,input_name):
    objects = bpy.data.objects
    chosen_name = input_name
    if "neg" in chosen_name or "pos" in chosen_name:
        chosen_name = chosen_name[0:-4]
    
    pending_cuts = []
    mesh_to_remove = []
    for cut in objects:
        cut.select = False
        if "cut" in cut.name:
            if "neg" in cut.name or "pos" in cut.name:
                if chosen_name == cut.name[0:-4]:
                    pending_cuts.append(cut)
                else:
                    mesh_to_remove.append(cut.name)
                    cut.select = True
            else:
                if chosen_name == cut.name:
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
        assist = bops.create_cuboid(bops.generate_cuboid_verts(x_max,x_min,y_max,y_min,z_max,z_min),"assist")
        div_level = config.tier_1_subdivision_level
        i = cut.name.count("_")
        if i>= 4:
            div_level = config.tier_3_subdivision_level
        elif i == 3:
            div_level = config.tier_2_subdivision_level
        else:
            div_level = config.tier_1_subdivision_level
        bops.perform_boolean_difference(assist,obj,div_level)
        
    intermediate_cleanup()

def rename_cuts(name):
    objects = bpy.data.objects
    for cut in objects:
        if "cut" in cut.name:
            if "pos" in cut.name:
                new_name = str.format("{}_pos", name)
                logger.add_choice_log(str.format("{} is renamed as {}",cut.name,new_name))
                cut.name = new_name
                cut.data.name = new_name
            elif "neg" in cut.name:
                new_name = str.format("{}_neg", name)
                logger.add_choice_log(str.format("{} is renamed as {}",cut.name,new_name))
                cut.name = new_name
                cut.data.name = new_name
            else:
                logger.add_choice_log(str.format("{} is renamed as {}",cut.name,name))
                cut.name = name
                cut.data.name = name
    logger.add_choice_log("")
    
def cut_main(cut_reqs,picks):
    volume = 1.0
    i = 0
    obj = bpy.context.active_object
    logger.log_start()
    
    for cut_req in cut_reqs:
        req_volume_ratio = cut_req["volume"]/volume
        req_aspect_ratio = cut_req["aspect"]
        req_aspects = []
        req_aspects.append(req_aspect_ratio[0]/req_aspect_ratio[1])
        req_aspects.append(req_aspect_ratio[2]/req_aspect_ratio[1])
        logger.add_matching_log(str.format("Level of divisions are {},{},{}", config.tier_1_divs,config.tier_2_divs,config.tier_3_divs))
        
        cutter.cutting_start(obj, req_volume_ratio, req_aspects)
        if picks[i] == 0:
            perform_best_cut(obj)
        elif picks[i] == 1:
            perform_picky_cut(obj,range(math.floor(config.allowed_pd_aspect*100),math.floor(config.mediocre_pd_cap*100)))
        else:
            perform_picky_cut(obj,range(math.floor(config.mediocre_pd_cap*100),math.floor(config.bad_pd_cap*100)))
            
        rename_cuts(str.format("component_{}", i+1))
        
        # TODO: use actual volume instead of req
        volume = volume-req_volume_ratio
        i += 1
        
        config.next_subdivision_level()
        
        logger.add_matching_separation()
        
    
def cut_debug_tree_main(cut_reqs,cut_name,num):
    volume = 1.0
    i = 0
    obj = bpy.context.active_object
    logger.log_start()
    
    for cut_req in cut_reqs:
        req_volume_ratio = cut_req["volume"]/volume
        req_aspect_ratio = cut_req["aspect"]
        req_aspects = []
        req_aspects.append(req_aspect_ratio[0]/req_aspect_ratio[1])
        req_aspects.append(req_aspect_ratio[2]/req_aspect_ratio[1])
        
        if i == num:
            logger.add_matching_log(str.format("Level of divisions are {},{},{}", config.tier_1_divs,config.tier_2_divs,config.tier_3_divs))
            
            cutter.cutting_start(obj, req_volume_ratio, req_aspects)
            perform_specific_cut(obj,cut_name)
                
            rename_cuts(str.format("component_{}", i+1))
            break
        
        volume = volume-req_volume_ratio
        i += 1
        config.next_subdivision_level()
    
"""
Perform only one cutting without separation for debugging purpose
"""
def cut_debug_main(cut_req,num):
    logger.log_start()
    for i in range(0,num):
        config.next_subdivision_level()
    
    obj = bpy.context.active_object
    
    req_volume_ratio = cut_req["volume"]
    req_aspect_ratio = cut_req["aspect"]
    req_aspects = []
    req_aspects.append(req_aspect_ratio[0]/req_aspect_ratio[1])
    req_aspects.append(req_aspect_ratio[2]/req_aspect_ratio[1])
    
    logger.add_matching_log(str.format("Level of divisions are {},{},{}", config.tier_1_divs,config.tier_2_divs,config.tier_3_divs))
    
    cutter.cutting_start(obj, req_volume_ratio, req_aspects)
            
            