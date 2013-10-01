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
   
""" Find one cut line from starting index onwards, exponential backoff is used here """ 
def get_cut_line(x_in,y_in,start_index,end_index):
    x = []
    y = []
    for i in range(start_index, end_index+1):
        x.append(x_in[i])
        y.append(y_in[i])
    return perform_leastsquare_fit(x,y)
        
def find_cut_lines(cutting_stripe_2D):
    limit_variance = 0.5
    
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
    
""" 
    Get point of intersection of 2 lines
    Lines are in format of [gradient, y-intercept, variance]
    or [INF, x-intercept, variance, if line is vertical]
    returned point is in the format of [x,y]
"""
def get_line_intersection(line1, line2): 
    # Both lines are vertical 
    if line1[0]=="INF" and line2[0]=="INF":
        return None
    # Lines are parallel
    elif math.fabs(line1[0]-line2[0]) <= 0.0001:
        return None
    elif line1[0]=="INF":
        x = line1[1]
        y = x*line2[0]+line2[1]
        return [x,y]
    elif line2[0]=="INF":
        x = line2[1]
        y = x*line1[0]+line1[1]
        return [x,y]
    # General case
    else:
        x = (line2[1]-line1[1])/(line1[0]-line2[0])
        y = x*line1[0]+line1[1]
        return [x,y]

def get_best_fringe_vertex(cut_line, x_bounds, y_bounds, ref_pt):
    candidates = []
    if cut_line[0] == "INF":
        candidates.append([cut_line[1],y_bounds[0]])
        candidates.append([cut_line[1],y_bounds[1]])
    elif math.fabs(cut_line[0]) <= 0.000001:
        candidates.append([x_bounds[0],cut_line[1]])
        candidates.append([x_bounds[1],cut_line[1]])
    else:
        min_x_pt = [x_bounds[0],cut_line[0]*x_bounds[0]+cut_line[1]]
        candidates.append(min_x_pt)
        max_x_pt = [x_bounds[1],cut_line[0]*x_bounds[1]+cut_line[1]]
        candidates.append(max_x_pt)
        min_y_pt = [(y_bounds[0]-cut_line[1])/cut_line[0],y_bounds[0]]
        candidates.append(min_y_pt)
        max_y_pt = [(y_bounds[1]-cut_line[1])/cut_line[0],y_bounds[1]]
        candidates.append(max_y_pt)
        
    min_dist_squared = math.pow(candidates[0][0]-ref_pt[0], 2)+math.pow(candidates[0][1]-ref_pt[1], 2)
    best_point = candidates[0]
    for i in candidates:
        dist_squared = math.pow(i[0]-ref_pt[0], 2)+math.pow(i[1]-ref_pt[1], 2)
        if dist_squared < min_dist_squared:
            min_dist_squared = dist_squared
            best_point = i
            
    return best_point
        
        
def get_cut_vertices(cut_lines,x_bounds,y_bounds,original_start,original_end):
    cut_vertices = []
    
    cut_vertices.append(get_best_fringe_vertex(cut_lines[0],x_bounds,y_bounds,original_start))
    
    if len(cut_lines)-2 >= 0:
        for i in range(0,len(cut_lines)-1):
            cut_vertices.append(get_line_intersection(cut_lines[i],cut_lines[i+1]))
    
    cut_vertices.append(get_best_fringe_vertex(cut_lines[-1],x_bounds,y_bounds,original_end))
        
    return cut_vertices
    

def transformer_testmain():
    """Get boundary vertices and edges of selected portion of model"""
    """
    Assume user is in EDIT mode.
    """
    #get vertices in boundary loop
    obj = bpy.context.active_object
    
    #get bound_box of object
    bound_box_vertices = []
    for i in obj.bound_box:
        bound_box_vertices.append(i)
        
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
    
    print(cut_lines)
    
    # +x and -x side of bound box is used here
    boundbox_px_verts = [bound_box_vertices[7],bound_box_vertices[6],bound_box_vertices[5],bound_box_vertices[4]]
    boundbox_nx_verts = [bound_box_vertices[0],bound_box_vertices[1],bound_box_vertices[2],bound_box_vertices[3]]
    x_min = boundbox_px_verts[0][1]
    x_max = boundbox_px_verts[0][1]
    y_min = boundbox_px_verts[0][2]
    y_max = boundbox_px_verts[0][2]
    for i in boundbox_px_verts:
        if i[1] > x_max:
            x_max = i[1]
        if i[1] < x_min:
            x_min = i[1]
        if i[2] > y_max:
            y_max = i[2]
        if i[2] < y_min:
            y_min = i[2]
    x_offset = (x_max - x_min)*0.1
    y_offset = (y_max - y_min)*0.1
    x_max = x_max + x_offset
    x_min = x_min - x_offset
    y_max = y_max + y_offset
    y_min = y_min - y_offset
    
    processed_cut_vertices = get_cut_vertices(cut_lines,[x_min,x_max],[y_min,y_max],cutting_stripe_2D[0],cutting_stripe_2D[-1])
    print (processed_cut_vertices)
    # 4 vertices of first plane, this plane will be extruded later
    plane_offset = (boundbox_px_verts[0][0]-boundbox_nx_verts[0][0])*0.1
    vert_1 = [boundbox_px_verts[0][0]+plane_offset, processed_cut_vertices[0][0],processed_cut_vertices[0][1]]
    vert_2 = [boundbox_px_verts[0][0]+plane_offset, processed_cut_vertices[1][0],processed_cut_vertices[1][1]]
    vert_3 = [boundbox_nx_verts[0][0]-plane_offset, processed_cut_vertices[0][0],processed_cut_vertices[0][1]]
    vert_4 = [boundbox_nx_verts[0][0]-plane_offset, processed_cut_vertices[1][0],processed_cut_vertices[1][1]]
    # Transformation to the cutting plane to be applied later
    obj_location = obj.location
    obj_scale = obj.scale
    obj_rotation_euler = obj.rotation_euler
        
    # Create cutting plane
    px_verts = [vert_1,vert_2,vert_3,vert_4]
    px_faces = [(0,1,3,2)]
    px_plane_mesh = bpy.data.meshes.new("Plane")
    px_plane_obj = bpy.data.objects.new("Cutting_plane", px_plane_mesh)
    bpy.context.scene.objects.link(px_plane_obj)
    px_plane_mesh.from_pydata(px_verts, [], px_faces)
    px_plane_mesh.update(calc_edges=True)
    
    # Select cutting plane
    obj.select = False
    cutting_plane = bpy.data.objects["Cutting_plane"]  
    bpy.context.scene.objects.active = cutting_plane
    cutting_plane.select = True
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    mesh = bmesh.from_edit_mesh(cutting_plane.data)
    
    # De-select all vertices, edges and faces
    for i in mesh.verts:
        i.select_set(False)
    for i in mesh.edges:
        i.select_set(False)
    for i in mesh.faces:
        i.select_set(False)    
        
    # Get the edge to be extruded
    edges = []
    for i in mesh.edges:
        if math.fabs(i.verts[0].co[1]-vert_2[1])<=0.00001 and math.fabs(i.verts[0].co[2]-vert_2[2])<=0.00001:
            if math.fabs(i.verts[1].co[1]-vert_2[1])<=0.00001 and math.fabs(i.verts[1].co[2]-vert_2[2])<=0.00001:
                edges.append(i)            
    
    if len(processed_cut_vertices) > 2:
        for i in range(1,len(processed_cut_vertices)-1):
            extrude_dir = [0,processed_cut_vertices[i+1][0]-processed_cut_vertices[i][0],processed_cut_vertices[i+1][1]-processed_cut_vertices[i][1]]
            # Perform extrude operation
            ret = bmesh.ops.extrude_edge_only(mesh,edges=edges)
            extruded_vertices = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
            extruded_edges = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMEdge)]
            
            bmesh.ops.translate(mesh,verts=extruded_vertices,vec=extrude_dir)
            
            edges = extruded_edges
    
    mesh.select_flush(True)
    bmesh.update_edit_mesh(cutting_plane.data, True)
    
    # Set transformation
    cutting_plane.location = obj_location
    cutting_plane.scale = obj_scale
    cutting_plane.rotation_euler = obj_rotation_euler
    
    print("***************END***************")
    print("***************BOOLEAN OPERATOR***************")
    
    # Make a copy of the object
    obj_name = obj.name
    copy_name = obj_name+'_copy'
    copy = bpy.data.objects.new(copy_name, bpy.data.meshes.new(copy_name))
    copy.data = obj.data.copy()
    copy.location = obj_location
    copy.scale = obj_scale
    copy.rotation_euler = obj_rotation_euler
    bpy.context.scene.objects.link(copy)
    
    # Set obj to be current active object
    cutting_plane.select = False
    obj.select = True
    bpy.context.scene.objects.active = obj
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.object.editmode_toggle()
    
    # Apply intersect to obtain one part of the cut
    bpy.ops.object.modifier_add(type='BOOLEAN')
    intersect_mod = obj.modifiers['Boolean']
    intersect_mod.operation = 'INTERSECT'
    intersect_mod.object = cutting_plane
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=intersect_mod.name)
    
    # Set copy to be current active object
    obj.select = False
    copy.select = True
    bpy.context.scene.objects.active = copy
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.object.editmode_toggle()
    
    # Apply difference to obtain the other part of the cut
    bpy.ops.object.modifier_add(type='BOOLEAN')
    difference_mod = copy.modifiers['Boolean']
    difference_mod.operation = 'DIFFERENCE'
    difference_mod.object = cutting_plane
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=difference_mod.name)
    
    print("***************END***************")
    
