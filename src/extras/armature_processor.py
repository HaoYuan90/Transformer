"""
import sys

mypath = "C:\\Users\\Xiaopewpew\\Desktop\\GithubProjects\\Transformer\\src\\extras"
sys.path.append(mypath)

ap_src_path = "C:/Users/Xiaopewpew/Desktop/GithubProjects/Transformer/src/extras/armature_processor.py"
exec(compile(open(ap_src_path).read(), "ap_src_path", 'exec'))

partitions = partition_armature(C.active_object)
"""

def get_bone_curr_childcount(bone):
    count = 0
    for bone in bone.children:
        if not bone["checked"]:
            count = count+1
    return count

def print_partitions(partitions):
    for partition in partitions:
        print(partition)

def partition_armature(armature):
    # Initialise armature data
    for bone in armature.data.bones:
        bone["checked"] = False
        bone["curr_childcount"] = 0
    
    partitions = []
    
    while True:
        # Update curr_childcount
        for bone in armature.data.bones:
            bone["curr_childcount"] = get_bone_curr_childcount(bone)

        # Get bones to start partitioning with
        starting_bones = []
        for bone in armature.data.bones:
            if not bone["checked"] and bone["curr_childcount"] == 0:
                starting_bones.append(bone)
                
        if len(starting_bones) == 0:
            break
        
        #print("starting bones:")
        #print(starting_bones)
    
        # Grow from starting bones   
        for bone in starting_bones:
            partition = []
            if "Link" not in bone.name and "link" not in bone.name:
                partition.append(bone)
            growth = bone.parent
            while growth != None:
                if "Link" not in growth.name and "link" not in growth.name:
                    if growth["curr_childcount"] > 1:
                        break
                    else:
                        partition.append(growth)
                else:
                    growth["checked"] = True
                growth = growth.parent
            for bone in partition:
                bone["checked"] = True
            partitions.append(partition)
    
    principle_bone = None
    for bone in armature.data.bones:
        if bone.parent == None:
            principle_bone = bone
            break
    
    if "Link" not in principle_bone.name and "link" not in principle_bone.name:
        if len(principle_bone.children) == 2:
            # Remove principle_bone from partitions
            to_remove = None
            for partition in partitions:
                if principle_bone in partition:
                    to_remove = partition
            partitions.remove(to_remove)
            # Join principle_bone with 2 children
            to_join = []
            for partition in partitions:
                if principle_bone.children[0].children[0] in partition:
                    to_join.append(partition)
                if principle_bone.children[1].children[0] in partition:
                    to_join.append(partition)
            #print("to join")
            #print(to_join)
            if len(to_join) == 2:
                partition = to_join[0] + [principle_bone] + to_join[1]
                partitions.append(partition)
                partitions.remove(to_join[0])
                partitions.remove(to_join[1])
                
    print_partitions(partitions)
    return partitions

