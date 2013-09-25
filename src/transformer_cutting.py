'''
@author: Jiang HaoYuan, National University of Singapore
'''

import bpy
import bmesh

import math
import vector_helper as vector
import arithmetic_helper as arith

""" Get angle between 2 vectors in 3d in radians """
def get_angle(v1, v2):
    """
    # Help with debugging
    v1 = [102,-1,50]
    v2 = [24,12,53]
    """
    if len(v1) != 3 or len(v2) != 3:
        print ("Vector inputs are not in 3D.")
        return
    v1_len = vector.length(v1)
    v2_len = vector.length(v2)
    if v1_len == 0 or v2_len == 0:
        print ("Invalid 0 vector.")
        return
    angle = math.acos(vector.vecdot(v1,v2)/(v1_len*v2_len))
    """
    # Help with debugging
    angle = angle/math.pi*180
    print(angle)
    """
    return angle


"""
    Get boundary loop of object
    Outputs indexes of vertices and edges in list passed in
"""
def select_boundary_loop(obj, cut_vertices, cut_edges):
    data = obj.data
    mesh = bmesh.from_edit_mesh(data)
    
    selected_vertices = [i for i in mesh.verts if i.select]
    selected_edges = [i for i in mesh.edges if i.select]
    selected_faces = [i for i in mesh.faces if i.select]
    unselected_edges = [i for i in mesh.edges if not i.select]
    
    for i in selected_faces:
        i.select_set(False)
    for i in selected_edges:
        i.select_set(False)
        
    for i in selected_vertices:
        i.select_set(False)
        for j in unselected_edges:
            if i in j.verts:
                i.select_set(True)
                cut_vertices.append(i.index)
                break
    for i in selected_edges:
        if i.verts[0].index in cut_vertices and i.verts[1].index in cut_vertices:
            i.select_set(True)
            cut_edges.append(i.index)
    
    """
    print(cut_vertices)
    print(len(cut_vertices))
    """
    mesh.select_flush(True)
    bmesh.update_edit_mesh(data, True)
    
    
""" Get vertices that starts a string or ends a string of edges in boundary loop """
def get_fringe_vertices(potential_cut_vertices, cut_edges):
    fv_indexes = []
    vertex_indexes = []
    for i in potential_cut_vertices:
        vertex_indexes.append(i.index)
      
    for i in cut_edges:
        if i.vertices[0] in vertex_indexes and i.vertices[1] not in vertex_indexes:
            fv_indexes.append(i.vertices[0])
        elif i.vertices[1] in vertex_indexes and i.vertices[0] not in vertex_indexes:
            fv_indexes.append(i.vertices[1])
    
    fringe_vertices = []
    for i in fv_indexes:
        for j in potential_cut_vertices:
            if j.index == i:
                fringe_vertices.append(j)
                break
            
    """
    print(fringe_vertices)
    """
    return fringe_vertices
    
""" Get vertex stripes of the fringe_vertices """
def get_vertex_stripes(fringe_vertices, potential_cut_vertices, cut_edges):
    vertex_stripes = []
    while fringe_vertices:
        curr_vertex = fringe_vertices[0]
        stripe = get_vertex_stripe(curr_vertex,potential_cut_vertices,cut_edges)
        vertex_stripes.append(stripe)
        fringe_vertices.remove(curr_vertex)
        if stripe[-1] in fringe_vertices:
            fringe_vertices.remove(stripe[-1])
        else:
            print("Unexpected error in get_vertex_stripes")
    return vertex_stripes

""" Get the vertex stripe of the starting_vertex """
def get_vertex_stripe(starting_vertex, potential_cut_vertices, cut_edges):
    vertex_indexes = []
    for i in potential_cut_vertices:
        vertex_indexes.append(i.index)
    stripe = []
    stripe.append(starting_vertex)
    
    next_vertex_found = True
    current_vertex = starting_vertex
    while next_vertex_found:
        next_vertex_found = False
        for i in cut_edges:
            index = -1
            if current_vertex.index == i.vertices[0] and i.vertices[1] in vertex_indexes:
                index = i.vertices[1]
            if current_vertex.index == i.vertices[1] and i.vertices[0] in vertex_indexes:
                index = i.vertices[0]
            if index != -1:
                for j in potential_cut_vertices:
                    if j.index == index and j not in stripe:
                        stripe.append(j)
                        next_vertex_found = True
                        current_vertex = j
                        break;
    print(stripe)
    return stripe

""" Do this later... """
def get_valid_vertex_stripe(vertex_stripes):
    if len(vertex_stripes) ==1:
        return vertex_stripes[0]
    else:
        print("do this later")

""" 
    Perform a leastsuqre fit on a set of points 
    Output is a list in the form
    [gradient, y-intercept, variance]
"""
def perform_leastsquare_fit(x,y):
    if len(x)!=len(y):
        print("Input to least square solver is invalid")
        return
    
    sum_x = arith.summation(x)
    sum_y = arith.summation(y)
    sum_xy = arith.mult_sum(x,y)
    sum_x_squared = arith.squared_sum(x)
    n = len(x)
    
    # Gradient of best-fit line
    m = (sum_xy - sum_x*sum_y/n)/(sum_x_squared-sum_x*sum_x/n)
    # Y-intercept of best-fit line 
    c = sum_y/n - m*sum_x/n
    # Estimated variance of best-fit line
    v = get_variance_leastsquare_fit(x,y,[m,c])
    
    return [m,c,v]

""" Get variance of least square fit solution """
def get_variance_leastsquare_fit(x,y,bestfit_line):
    squared_residual = []
    for i in range(len(x)):
        squared_residual.append(math.pow(y[i]-bestfit_line[0]*x[i]-bestfit_line[1], 2))
        
    return arith.summation(squared_residual)/(len(x)-2)
    

def transformer_testmain():
    """Get boundary vertices and edges of selected portion of model"""
    """
    Assume user is in EDIT mode.
    """
    #get vertices in boundary loop
    obj = bpy.context.active_object
    cut_vertices_indexes = []
    cut_edges_indexes = []
    select_boundary_loop(obj,cut_vertices_indexes,cut_edges_indexes)
    
    """
    print(cut_vertices_indexes)
    print(cut_edges_indexes)
    """
    
    cut_vertices = []
    cut_edges = []
    
    for i in cut_vertices_indexes:
        cut_vertices.append(obj.data.vertices[i])
    for j in cut_edges_indexes:
        cut_edges.append(obj.data.edges[j])
        

    """
    print(cut_vertices)
    print(len(cut_vertices))
    print(cut_edges)
    print(len(cut_edges))
    """
    
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
    
    angle_threshold = math.pi/4
    plane_normal = [1,0,0]
    
    # Vertices that may be used to compute the best fit cutting plane
    potential_cut_vertices = [];
    for i in obj.data.polygons:
        for j in cut_vertices:
            if j not in potential_cut_vertices:
                if j.index in i.vertices:
                    if (get_angle(plane_normal,i.normal)) < angle_threshold:
                        potential_cut_vertices.append(j)
    
    """
    print(len(potential_cut_vertices))
    """
    fringe_vertices = get_fringe_vertices(potential_cut_vertices, cut_edges)
    vertex_stripes = get_vertex_stripes(fringe_vertices, potential_cut_vertices, cut_edges)
    print(vertex_stripes)
    
    cutting_stripe = get_valid_vertex_stripe(vertex_stripes)
    
    print("***************END***************")
    
                
    
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
        
