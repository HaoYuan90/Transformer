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

"""
Rename cut obtained and set origin to center of mass
"""
def process_cutting_results(name):
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
            bops.set_object_origin(cut)
    logger.add_choice_log("")
    
"""
Used to process the last object left over by cutting
Not used in any of the debugging method, requires the last bone
"""
def process_object(obj,name):
    logger.add_choice_log(str.format("{} is renamed as {}",obj.name,name))
    obj.name = name
    obj.data.name = name
    bops.set_object_origin(obj)
    
def position_objects_to_bones(bones,bone_prefix):
    for bone in bones:
        pos = (bone.head_local + bone.tail_local)/2
        obj = bpy.data.objects[bone.name.replace(bone_prefix,'')]
        if obj != None:
            obj.location = pos
        else:
            logger.add_error_log("Cant find object at position_objects_to_bones")
    
"""
Sequence: 
object which on other objects have it as parent (sym first, smallest first)
get its (sym first, smallest first) children
following this, cut layer by layer
"""
def process_armature(armature):
    # Initialise armature data
    for bone in armature.data.bones:
        bone["is_parent"] = len(bone.children) > 0
        bone["has_cut"] = False
    
    potential_bone_list = []
    for bone in armature.data.bones:
        if bone["is_parent"] == False:
            potential_bone_list.append(bone)

    if len(potential_bone_list) <= 0:
        logger.add_error_log("Error, no potential bone found at process_armature")
        return
    for bone in potential_bone_list:
        if "Link" in bone.name or "link" in bone.name:
            potential_bone_list.remove(bone)
            logger.add_error_log("Error, linking bone found at edge positions, check armature")
    
    starting_bone = potential_bone_list[0]
    is_starting_sym = "pos" in starting_bone.name or "neg" in starting_bone.name
    for bone in potential_bone_list:
        is_sym = "pos" in bone.name or "neg" in bone.name
        if is_sym and not is_starting_sym:
            starting_bone = bone
            is_starting_sym = True
        elif (is_sym and is_starting_sym) or (not is_sym and not is_starting_sym):
            if bone["component_volume"] < starting_bone["component_volume"]:
                starting_bone = bone
    
    sequence = []
    sequence.append(starting_bone)
    bone = starting_bone.parent
    while bone != None:
        if "Link" not in bone.name and "link" not in bone.name:
            sequence.append(bone)
        bone = bone.parent
    return sequence

"""
Default values are set for debugging purposes
"""
def cutting_main(picks = [0,0],armature_name = "Armature",object_name = "Cube",bone_prefix = "Bone_"):
    logger.log_start()
    
    armature = bpy.data.objects[armature_name]
    obj = bpy.data.objects[object_name]
    if armature == None or obj == None:
        logger.add_error_log("Invalid input names")
        return
    
    sequence = process_armature(armature)

    cut_reqs = []
    for bone in sequence:
        if "component_volume" in bone:
            cut_reqs.append({"volume":bone["component_volume"],"aspect":bone["component_aspect"],"name":bone.name.replace(bone_prefix,'')})
        elif sequence.index(bone) != len(sequence)-1:
            logger.add_error_log("Bones with no cutting reqs must be the last bone in the tree for testing")
            return
    
    cutting_start(obj,cut_reqs,picks)
    
    # Process the last object
    process_object(obj,sequence[len(sequence)-1].name.replace(bone_prefix,''))
    
    # Put objects in right places
    position_objects_to_bones(sequence,bone_prefix)
        
def cutting_start(obj,cut_reqs,picks):
    volume = 1.0
    i = 0
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
        
        if "name" in cut_req:
            process_cutting_results(cut_req["name"])
        else:
            process_cutting_results(str.format("component_{}", i+1))
        
        # TODO: use actual volume instead of req
        volume = volume-req_volume_ratio
        i += 1
        config.next_subdivision_level()
        logger.add_matching_separation()
        
def cutting_debug(cut_reqs,picks,obj = bpy.context.active_object):
    logger.log_start()
    cutting_start(obj,cut_reqs,picks)
    
def cutting_debug_tree(cut_reqs,cut_name,num,obj = bpy.context.active_object):
    logger.log_start()
    volume = 1.0
    i = 0
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
                
            process_cutting_results(str.format("component_{}", i+1))
            break
        
        volume = volume-req_volume_ratio
        i += 1
        config.next_subdivision_level()
    
"""
Perform only one cutting without separation for debugging purpose
"""
def cutting_debug_1p(cut_req,num,obj = bpy.context.active_object):
    logger.log_start()
    for i in range(0,num):
        config.next_subdivision_level()
    
    req_volume_ratio = cut_req["volume"]
    req_aspect_ratio = cut_req["aspect"]
    req_aspects = []
    req_aspects.append(req_aspect_ratio[0]/req_aspect_ratio[1])
    req_aspects.append(req_aspect_ratio[2]/req_aspect_ratio[1])
    
    logger.add_matching_log(str.format("Level of divisions are {},{},{}", config.tier_1_divs,config.tier_2_divs,config.tier_3_divs))
    
    cutter.cutting_start(obj, req_volume_ratio, req_aspects)
            
            