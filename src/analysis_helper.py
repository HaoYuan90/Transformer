import bpy
import math

"""
DEPENDENCY : http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Mesh/VolumeTools
"""

# Debug messages control
DEBUG_ANALYTICS = False

def analyse_volume_approximation(object, divisions, estimated_volume_ratios):
    if DEBUG_ANALYTICS:
        volume_ratios = []
        pds = []
        # Set cuboid to be current active object
        object.select = True
        bpy.context.scene.objects.active = object
        bpy.ops.object.volume()
        total_volume = object['volume']
        object.select = False
        
        for division in divisions:
            division.select = True
            bpy.context.scene.objects.active = division
            bpy.ops.object.volume()
            volume_ratios.append(division['volume']/total_volume)
            division.select = False
        
        for i in range(0,len(estimated_volume_ratios)):
            pd = math.fabs((estimated_volume_ratios[i] - volume_ratios[i])/volume_ratios[i])
            pds.append(pd)
        
        print(str.format("Estimated volume: {}", estimated_volume_ratios))
        print(str.format("Actual volume: {}", volume_ratios))
        print(str.format("Percentage discrepancy: {}", pds))
