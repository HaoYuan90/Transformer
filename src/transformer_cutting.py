'''
@author: Jiang HaoYuan, National University of Singapore
'''

import bpy
import bmesh

import math
import vector_helper as vector
import arithmetic_helper as arith

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
    denom = sum_x_squared-sum_x*sum_x/n
    if denom != 0:
        m = (sum_xy - sum_x*sum_y/n)/denom
        # Y-intercept of best-fit line 
        c = sum_y/n - m*sum_x/n
        # Estimated variance of best-fit line
        v = get_variance_leastsquare_fit(x,y,[m,c])
        return [m,c,v]
    else:
        m = "INF"
        # When the line has infinite gradient, c = x-intercept
        c = sum_x/n
        v = get_variance_leastsquare_fit(x,y,[m,c])
        return [m,c,v]

""" Get variance of least square fit solution """
def get_variance_leastsquare_fit(x,y,bestfit_line):
    squared_residual = []
    if bestfit_line[0]!="INF":
        for i in range(len(x)):
            squared_residual.append(math.pow(y[i]-bestfit_line[0]*x[i]-bestfit_line[1], 2))
    else:
        for i in range(len(x)):
            squared_residual.append(math.pow(x[i]-bestfit_line[1], 2))
        
    return arith.summation(squared_residual)/(len(x))
    
def get_cut_line(x_in,y_in,start_index,end_index):
    x = []
    y = []
    for i in range(start_index, end_index+1):
        x.append(x_in[i])
        y.append(y_in[i])
    return perform_leastsquare_fit(x,y)
        
def find_cut_lines(cutting_stripe_2D):
    limit_variance = 0.000001
    
    curr_index = 0
    end_index = len(cutting_stripe_2D)-1
    x = []
    y = []
    for i in cutting_stripe_2D:
        x.append(i[0])
        y.append(i[1])
    
    cut_lines = []
    prev_line = None
    last_succeeded = False
    while True:
        if end_index == len(cutting_stripe_2D):
            cut_lines.append(prev_line)
            break
        
        line = get_cut_line(x,y,curr_index,end_index)
        if line[2] > limit_variance:
            if last_succeeded :
                last_succeeded = False
                cut_lines.append(prev_line)
                curr_index = end_index-1
                end_index = len(cutting_stripe_2D)-1
            end_index = math.floor((end_index+curr_index)/2)
        else:
            end_index += 1
            last_succeeded = True
            prev_line = line
    
    return cut_lines
        
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
    
    angle_threshold = math.pi/4
    plane_normal = [1,0,0]
    
    # Vertices that may be used to compute the best fit cutting plane
    potential_cut_vertices = [];
    for i in obj.data.polygons:
        for j in cut_vertices:
            if j not in potential_cut_vertices:
                if j.index in i.vertices:
                    if (vector.vecangle(plane_normal,i.normal)) < angle_threshold:
                        potential_cut_vertices.append(j)
    
    """
    print(len(potential_cut_vertices))
    """
    fringe_vertices = get_fringe_vertices(potential_cut_vertices, cut_edges)
    vertex_stripes = get_vertex_stripes(fringe_vertices, potential_cut_vertices, cut_edges)
    print(vertex_stripes)
    
    cutting_stripe = get_valid_vertex_stripe(vertex_stripes)
    # Extract the coordinates we are interested in according to cut plane, y z for now
    cutting_stripe_2D = []
    for i in cutting_stripe:
        cutting_stripe_2D.append([i.co[1],i.co[2]])
    
    cut_lines = find_cut_lines(cutting_stripe_2D)
        
    print("***************END***************")
    
    return cut_lines
   
    
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
        
