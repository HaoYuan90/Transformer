import bpy

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
Set object's origin to its center of mass
"""
def set_object_origin(obj):
    # Set obj_to to be current active object
    obj.select = True
    bpy.context.scene.objects.active = obj
    bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY')
    obj.select = False

"""
Perform blender's boolean operation
obj_from is the object parameter in boolean operation
obj_to is the object which operator is applied to
level is the level of subdivision on the to object
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
    
    
"""
Perform blender's boolean operation
obj_from is the object parameter in boolean operation
obj_to is the object which operator is applied to
level is the level of subdivision on the from object
"""
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