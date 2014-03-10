"""
    #vertices of bounding box bounding_vertices
    bv = []
    for i in obj.bound_box:
        bv.append(i)
        
    #draw a +x plane of bounding box
    px_verts = [bv[7],bv[6],bv[5],bv[4]]
    px_faces = [(0,1,2,3)]
    px_plane_mesh = bpy.data.meshes.new("Plane")
    px_plane_obj = bpy.data.objects.new("positive_x", px_plane_mesh)
    px_plane_obj.location = obj.location
    px_plane_obj.scale = obj.scale*1.1
    px_plane_obj.rotation_euler = obj.rotation_euler
    bpy.context.scene.objects.link(px_plane_obj)
    px_plane_mesh.from_pydata(px_verts, [], px_faces)
    px_plane_mesh.update(calc_edges=True)
    
    #draw a -x plane of bounding box
    nx_verts = [bv[0],bv[1],bv[2],bv[3]]
    nx_faces = [(0,1,2,3)]
    nx_plane_mesh = bpy.data.meshes.new("Plane")
    nx_plane_obj = bpy.data.objects.new("negative_x", nx_plane_mesh)
    nx_plane_obj.location = obj.location
    nx_plane_obj.scale = obj.scale*1.1
    nx_plane_obj.rotation_euler = obj.rotation_euler
    bpy.context.scene.objects.link(nx_plane_obj)
    nx_plane_mesh.from_pydata(nx_verts, [], nx_faces)
    nx_plane_mesh.update(calc_edges=True)
    
    #draw a -y plane of bounding box
    ny_verts = [bv[1],bv[0],bv[4],bv[5]]
    ny_faces = [(0,1,2,3)]
    ny_plane_mesh = bpy.data.meshes.new("Plane")
    ny_plane_obj = bpy.data.objects.new("negative_y", ny_plane_mesh)
    ny_plane_obj.location = obj.location
    ny_plane_obj.scale = obj.scale*1.1
    ny_plane_obj.rotation_euler = obj.rotation_euler
    bpy.context.scene.objects.link(ny_plane_obj)
    ny_plane_mesh.from_pydata(ny_verts, [], ny_faces)
    ny_plane_mesh.update(calc_edges=True)
    #draw a +y plane of bounding box
    py_verts = [bv[3],bv[2],bv[6],bv[7]]
    py_faces = [(0,1,2,3)]
    py_plane_mesh = bpy.data.meshes.new("Plane")
    py_plane_obj = bpy.data.objects.new("positive_y", py_plane_mesh)
    py_plane_obj.location = obj.location
    py_plane_obj.scale = obj.scale*1.1
    py_plane_obj.rotation_euler = obj.rotation_euler
    bpy.context.scene.objects.link(py_plane_obj)
    py_plane_mesh.from_pydata(py_verts, [], py_faces)
    py_plane_mesh.update(calc_edges=True)
    #draw a -z plane of bounding box
    nz_verts = [bv[7],bv[4],bv[0],bv[3]]
    nz_faces = [(0,1,2,3)]
    nz_plane_mesh = bpy.data.meshes.new("Plane")
    nz_plane_obj = bpy.data.objects.new("negative_z", nz_plane_mesh)
    nz_plane_obj.location = obj.location
    nz_plane_obj.scale = obj.scale*1.1
    nz_plane_obj.rotation_euler = obj.rotation_euler
    bpy.context.scene.objects.link(nz_plane_obj)
    nz_plane_mesh.from_pydata(nz_verts, [], nz_faces)
    nz_plane_mesh.update(calc_edges=True)
    #draw a +z plane of bounding box
    pz_verts = [bv[5],bv[6],bv[2],bv[1]]
    pz_faces = [(0,1,2,3)]
    pz_plane_mesh = bpy.data.meshes.new("Plane")
    pz_plane_obj = bpy.data.objects.new("positive_z", pz_plane_mesh)
    pz_plane_obj.location = obj.location
    pz_plane_obj.scale = obj.scale*1.1
    pz_plane_obj.rotation_euler = obj.rotation_euler
    bpy.context.scene.objects.link(pz_plane_obj)
    pz_plane_mesh.from_pydata(pz_verts, [], pz_faces)
    pz_plane_mesh.update(calc_edges=True)
"""

# Show selected vertices/change selection
"""
    obj = bpy.context.active_object.data
    mesh = bmesh.from_edit_mesh(obj)
    
    selected_vertices = [i for i in mesh.verts if i.select]
    selected_edges = [i for i in mesh.edges if i.select]
    selected_faces = [i for i in mesh.faces if i.select]
    unselected_edges = [i for i in mesh.edges if not i.select]
    cut_vertices = []
    
    for i in selected_faces:
        i.select_set(False)
    for i in selected_edges:
        i.select_set(False)
    for i in selected_vertices:
        i.select_set(False)
        for j in unselected_edges:
            if i in j.verts:
                i.select_set(True)
                cut_vertices.append(i)
                break
    print(cut_vertices)
    print(len(cut_vertices))
    
    mesh.select_flush(True)
    
    bmesh.update_edit_mesh(obj, True)
"""


# Extrude related
"""
  obj = bpy.context.active_object

  bv = []
  for i in obj.bound_box:
      bv.append(i)
      
  #draw a +x plane of bounding box
  px_verts = [bv[7],bv[6],bv[5],bv[4]]
  px_faces = [(0,1,2,3)]
  px_plane_mesh = bpy.data.meshes.new("Plane")
  px_plane_obj = bpy.data.objects.new("positive_x", px_plane_mesh)
  px_plane_obj.location = obj.location
  px_plane_obj.scale = obj.scale*1.1
  px_plane_obj.rotation_euler = obj.rotation_euler
  bpy.context.scene.objects.link(px_plane_obj)
  px_plane_mesh.from_pydata(px_verts, [], px_faces)
  px_plane_mesh.update(calc_edges=True)
  
  obj.select = False
  
  plane = bpy.data.objects["positive_x"]  
  bpy.context.scene.objects.active = plane
  
  plane.select = True
  bpy.ops.object.mode_set(mode = 'EDIT')
  
  mesh = bmesh.from_edit_mesh(plane.data)
  
  for i in mesh.verts:
      i.select_set(False)
  for i in mesh.edges:
      i.select_set(False)
  for i in mesh.faces:
      i.select_set(False)
  
  mesh.verts[0].select_set(True)
  mesh.verts[1].select_set(True)
  
  for i in mesh.edges:
      if mesh.verts[0] in i.verts and mesh.verts[1] in i.verts:
          i.select_set(True)
  
  mesh.select_flush(True)
  
  bmesh.update_edit_mesh(plane.data, True)
  
  bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"mirror":False},TRANSFORM_OT_translate={"value":[1,1,1]})
"""
  
"""
  obj = bpy.context.active_object.data
  bpy.ops.object.mode_set(mode = 'EDIT')
  
  mesh = bmesh.from_edit_mesh(obj)
  
  for i in mesh.verts:
      i.select_set(False)
  for i in mesh.edges:
      i.select_set(False)
  for i in mesh.faces:
      i.select_set(False)
  
  edges = []
  for i in mesh.edges:
      if mesh.verts[0] in i.verts and mesh.verts[1] in i.verts:
          edges.append(i)
  
  newEdge = None  
  ret = bmesh.ops.extrude_edge_only(mesh,edges=edges)
  
  extruded_vertices = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
  
  bmesh.ops.translate(mesh,verts=extruded_vertices,vec=(0.0, 0.0, 1.0))
  
  mesh.select_flush(True)
  bmesh.update_edit_mesh(obj, True)
  
  #bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"mirror":False},TRANSFORM_OT_translate={"value":(1,1,1)})
"""
      