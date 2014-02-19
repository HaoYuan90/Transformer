import bpy
import math

import transformer_config as config

"""
DEPENDENCY : http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Mesh/VolumeTools
"""

def analyse_volume_approximation(object, divisions, estimated_volume_ratios, logger):
    logger.add_analytic_log(object.name)
    logger.add_analytic_log(str.format("Estimated volume: {}", estimated_volume_ratios))
    if config.DEBUG_ANALYTICS:
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
        
        """
        for i in range(0,len(estimated_volume_ratios)):
            pd = math.fabs((estimated_volume_ratios[i] - volume_ratios[i])/volume_ratios[i])
            pds.append(pd)
        """
        logger.add_analytic_log(str.format("Actual volume: {}", volume_ratios))
        logger.add_analytic_log(str.format("Percentage discrepancy: {}", pds))
