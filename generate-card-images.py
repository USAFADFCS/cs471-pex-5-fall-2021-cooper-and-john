import bpy
import bmesh
from random import random, choice
import math
from mathutils import Euler, Matrix, Vector
import os
import shutil

project_folder = "C:\\Users\\C23Cooper.Hammond\\Documents\\dev\\USAFA\\CS471\\cs471-pex-5-fall-2021-cooper-and-john\\"
scene = bpy.context.scene

card_faces = [2, 3, 4, 5, 6, 7, 8, 9, 10, "jack", "queen", "king", "ace"]
suits = ["clubs", "diamonds", "hearts", "spades"]
classes = []
for suit in suits:
    for card in card_faces:
        classes.append(f"{card}_of_{suit}")

def clear_scene():
    objs = bpy.data.objects
    for obj in objs:
        objs.remove(obj, do_unlink=True)
        
    for material in bpy.data.materials:
        bpy.data.materials.remove(material, do_unlink=True)
        
    for image in bpy.data.images:
        bpy.data.images.remove(image, do_unlink=True)
        
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh, do_unlink=True)
        
    for texture in bpy.data.textures:
        bpy.data.textures.remove(texture, do_unlink=True)
        
    for camera in bpy.data.cameras:
        bpy.data.cameras.remove(camera, do_unlink=True)

def create_light(location, brightness):
    light_data = bpy.data.lights.new(name="my-light-data", type='POINT')
    light_data.energy = brightness

    light_object = bpy.data.objects.new(name="my-light", object_data=light_data)
    bpy.context.collection.objects.link(light_object)
    light_object.location = location

def create_camera(location, rotation):
    camera_data = bpy.data.cameras.new(name='Camera')
    camera_object = bpy.data.objects.new('Camera', camera_data)
    bpy.context.scene.collection.objects.link(camera_object)
    camera_object.location = location
    camera_object.rotation_euler = Euler(rotation, 'XYZ')
    
    return camera_object

def point_camera(obj, target, roll=0):
    if not isinstance(target, Vector):
        target = Vector(target)
    loc = obj.location
    # direction points from the object to the target
    direction = target - loc

    quat = direction.to_track_quat('-Z', 'Y')
    
    # /usr/share/blender/scripts/addons/add_advanced_objects_menu/arrange_on_curve.py
    quat = quat.to_matrix().to_4x4()
    rollMatrix = Matrix.Rotation(roll, 4, 'Z')

    # remember the current location, since assigning to obj.matrix_world changes it
    loc = loc.to_tuple()
    #obj.matrix_world = quat * rollMatrix
    # in blender 2.8 and above @ is used to multiply matrices
    # using * still works but results in unexpected behaviour!
    obj.matrix_world = quat @ rollMatrix
    obj.location = loc

def create_bg_object(scale):
    x = 7 * scale
    y = 7 * scale
    
    width, depth, height = (x, y, 0)
    
    bpy.ops.mesh.primitive_plane_add()
    ob = bpy.context.object
    ob.name = "background"
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    
    bm.edges.ensure_lookup_table()
    
    bmesh.ops.scale(
        bm,
        verts = bm.verts,
        vec = (width, depth, height),
    )
    
    location_transform = (0, 0, -.005)
    bmesh.ops.transform(
        bm,
        matrix=Matrix.Translation(location_transform),
        space=bpy.context.object.matrix_world, 
        verts=bm.verts
    )
    
    rotation_transform = (0, 0, 0)
    bmesh.ops.rotate(
        bm,
        verts=bm.verts,
        cent=(0,0,0),
        matrix=Matrix.Rotation(math.radians(random() * 360), 3, 'Z')
    )
    
    bm.to_mesh(me)
    
    return ob   

def create_card_object(scale, center=True):
    corner_rad = .15
    x = 500.0/726.0 * scale
    y = 1 * scale
    
    corner_radius = corner_rad
    corner_segments = 5
    width, depth, height = (x, y, 0)

    bpy.ops.mesh.primitive_plane_add()
    ob = bpy.context.object
    ob.name = "card"
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)

    bm.edges.ensure_lookup_table()
    # scale first to keep corners round
    bmesh.ops.scale(
        bm,
        verts=bm.verts,
        vec=(width, depth, height),
    )

    bpy.ops.object.modifier_add(type='BEVEL')
    bevel_mod = ob.modifiers['Bevel']
    bevel_mod.affect = 'VERTICES'
    bevel_mod.segments = 5
    bevel_mod.width = corner_rad
      
    bm.to_mesh(me)
    card = ob
    
    corner1 = get_corner('corner1', scale)
    corner2 = get_corner('corner2', scale, inverse=True)
    
    return card, corner1, corner2

def get_corner(name, scale, inverse=False):
    size_scale = .23 * scale
    ratio = 1.1/2
    x = ratio * size_scale
    y = 1 * size_scale
    size_scale_vect = (x, y, 0)
    
    bpy.ops.mesh.primitive_plane_add()
    corner = bpy.context.object
    corner.name = name
    me = corner.data
    bm = bmesh.new()
    bm.from_mesh(me)
    
    bm.edges.ensure_lookup_table()
    bmesh.ops.scale(
        bm,
        verts=bm.verts,
        vec=size_scale_vect
    )
    
    if inverse:
        scale *= -1    

    location_transform = (-.545 * scale, .732 * scale, -.001)
    bmesh.ops.transform(
        bm,
        matrix=Matrix.Translation(location_transform),
        space=bpy.context.object.matrix_world, 
        verts=bm.verts
    )
    bm.to_mesh(me)
    
    return corner

def attach_material(object, image_path):
    bpy.ops.material.new()
    mat = bpy.data.materials[-1]
    mat.name = object.name
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # RENDERING NODES
    node_tex_coord = nodes.new('ShaderNodeTexCoord')
    node_tex_coord.location = (-500,0)

    node_tex_mapping = nodes.new('ShaderNodeMapping')
    node_tex_mapping.location = (-250,0)
    # inputs[1] is location
    #node_tex_mapping.inputs[1].default_value[0] = -2.5
    #node_tex_mapping.inputs[1].default_value[1] = -2.0
    # inputs[3] is scale
    #node_tex_mapping.inputs[3].default_value[0] = 4
    #node_tex_mapping.inputs[3].default_value[1] = 4

    node_tex = nodes.new('ShaderNodeTexImage')
    node_tex.image = bpy.data.images.load(image_path)
    node_tex.location = (0,0)

    node_principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_principled_bsdf.location = (250,0)
    node_principled_bsdf.inputs[5].default_value = 0
    node_principled_bsdf.inputs[7].default_value = 0
    node_principled_bsdf.inputs[11].default_value = 0
    node_principled_bsdf.inputs[13].default_value = 0

    node_output = nodes.new(type='ShaderNodeOutputMaterial')   
    node_output.location = (500,0)

    # linking nodes
    links = mat.node_tree.links
    links.new(node_tex_coord.outputs["UV"], node_tex_mapping.inputs["Vector"])
    links.new(node_tex_mapping.outputs["Vector"], node_tex.inputs["Vector"])
    links.new(node_tex.outputs["Color"], node_principled_bsdf.inputs["Base Color"])
    links.new(node_principled_bsdf.outputs["BSDF"], node_output.inputs["Surface"])

    object.active_material = mat

def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))

def camera_view_bounds_2d(scene, cam_ob, me_ob, class_):
    mat = cam_ob.matrix_world.normalized().inverted()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh_eval = me_ob.evaluated_get(depsgraph)
    me = mesh_eval.to_mesh()
    me.transform(me_ob.matrix_world)
    me.transform(mat)

    camera = cam_ob.data
    frame = [-v for v in camera.view_frame(scene=scene)[:3]]
    camera_persp = camera.type != 'ORTHO'

    lx = []
    ly = []

    for v in me.vertices:
        co_local = v.co
        z = -co_local.z

        if camera_persp:
            if z == 0.0:
                lx.append(0.5)
                ly.append(0.5)
            # Does it make any sense to drop these?
            # if z <= 0.0:
            #    continue
            else:
                frame = [(v / (v.z / z)) for v in frame]

        min_x, max_x = frame[1].x, frame[2].x
        min_y, max_y = frame[0].y, frame[1].y

        x = (co_local.x - min_x) / (max_x - min_x)
        y = (co_local.y - min_y) / (max_y - min_y)

        lx.append(x)
        ly.append(y)

    min_x = clamp(min(lx), 0.0, 1.0)
    max_x = clamp(max(lx), 0.0, 1.0)
    min_y = clamp(min(ly), 0.0, 1.0)
    max_y = clamp(max(ly), 0.0, 1.0)

    mesh_eval.to_mesh_clear()

    r = scene.render
    fac = r.resolution_percentage * 0.01
    dim_x = r.resolution_x * fac
    dim_y = r.resolution_y * fac

    # Sanity check
    if round((max_x - min_x) * dim_x) == 0 or round((max_y - min_y) * dim_y) == 0:
        return {"x": 0, "y": 0, "w": 0, "h": 0, "class": class_}

    return {
        "x":round(min_x * dim_x),            # X
        "y":round(dim_y - max_y * dim_y),    # Y
        "w":round((max_x - min_x) * dim_x),  # Width
        "h":round((max_y - min_y) * dim_y),  # Height
        "class": class_
    }

def show_rects(image, rects):
    import cv2

    image = cv2.imread(image)
    
    color = (0,0,255)
    thickness = 1
    
    #print(rects)
    
    for rect in rects:
        start = (rect["x"], rect["y"])
        end = (rect["x"] + rect["w"], rect["y"] + rect["h"])

        image = cv2.rectangle(image, start, end, color, thickness)
    
    cv2.imshow('Rectangle',image)

def render_scene(filepath, resolution):
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.resolution_percentage = resolution * 100
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still = 1)

    return bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y

def random_image_from_dir(dir):
    images = [image for image in os.listdir(dir)]
    image_choice = choice(images)
    return image_choice

def make_random_background(scale):
    bg = create_bg_object(scale)
    attach_material(bg, project_folder + "bgs\\" + random_image_from_dir(project_folder + "bgs\\"))
    #attach_material(bg, project_folder + "bgs\\20211207_145829.jpg")

def make_random_camera(scale, origin=(0,0,0), sphere_range=(10, 15), aiming_range=3):
    r = sphere_range[0] + random() * sphere_range[1] * scale
    inclination = (random() * 120 - 60) * math.pi/180
    azimuth = (random() * 360) * math.pi/180
    
    loc = (
        r*math.cos(azimuth)*math.sin(inclination) + origin[0],
        r*math.sin(azimuth)*math.sin(inclination) + origin[0],
        r*math.cos(inclination) + origin[0]
    )
    
    camera = create_camera(loc, (0,0,0))
    point_camera(camera, (
        random() * aiming_range - aiming_range/2.0, 
        random() * aiming_range - aiming_range/2.0, 
        random() * aiming_range - aiming_range/2.0
    ))
    
    return camera
   
def make_random_light(scale, origin=(0,0,0), sphere_range=(10, 15), brightness_range=(100,1000)):
    r = sphere_range[0] + random() * (sphere_range[1] - sphere_range[0]) * scale
    inclination = (random() * 150 - 75) * math.pi/180
    azimuth = (random() * 360) * math.pi/180
    
    loc = (
        r*math.cos(azimuth)*math.sin(inclination) + origin[0],
        r*math.sin(azimuth)*math.sin(inclination) + origin[0],
        r*math.cos(inclination) + origin[0]
    )
    
    camera = create_light(loc, 14000)
    #random() * (brightness_range[1] - brightness_range[0]) + brightness_range[0])

    return camera

def make_random_card(scale):
    card_pics_path = project_folder + "pics\\"
    card_image = random_image_from_dir(card_pics_path)

    while card_image.endswith("2.png"):
        card_image = random_image_from_dir(card_pics_path)
        # TODO: handle special corner loc data for face cards

    image_path = card_pics_path + card_image
    card_class = card_image.strip(".png")

    card_object, corner1, corner2 = create_card_object(scale)
    attach_material(card_object, image_path)

    bounding_boxes = [
        camera_view_bounds_2d(scene, scene.camera, corner1, card_class), 
        camera_view_bounds_2d(scene, scene.camera, corner2, card_class)
    ]
    
    return card_object, bounding_boxes

def generate_random_scene(name, image_output_dir, labels_output_dir, scale, resolution=.3, show_bounding_boxes=False):
    clear_scene()

    # SET UP SCENE
    make_random_background(scale)
    make_random_light(scale)
    scene.camera = make_random_camera(scale)
    card_object, card_bounding_boxes = make_random_card(scale)
    
    # render image
    output_image_file_name = image_output_dir + name + ".jpg"
    image_width, image_height = render_scene(output_image_file_name, resolution)
    
    # save labels
    output_label_file_name = labels_output_dir + name + ".txt"
    label_str = ""
    for bounding_box in card_bounding_boxes:
        if bounding_box["x"] == 0 or bounding_box["y"] == 0:
            pass

        class_index = classes.index(bounding_box["class"])
        x_center = (bounding_box["x"] + bounding_box["w"] / 2) / image_width
        y_center = (bounding_box["y"] + bounding_box["h"] / 2) / image_height
        width = bounding_box["w"] / image_width
        height = bounding_box["h"] / image_height
        label_str += f"{class_index} {x_center} {y_center} {width} {height}\n"

    label_file = open(output_label_file_name, "w")
    label_file.write(label_str)
    label_file.close()
    
    if show_bounding_boxes:
        show_rects(output_image_file_name, card_bounding_boxes)

def setup_folder_structure(clear_data_folder=False):
    data_folder = project_folder + "model-data\\"

    folders = ["test", "train", "validate"]

    os.makedirs(data_folder, exist_ok=True)

    for folder in folders:
        folder = data_folder + folder + "\\"

        os.makedirs(folder + "images", exist_ok=True)
        os.makedirs(folder + "labels", exist_ok=True)

    shutil.copy(project_folder + "data.yaml", data_folder)

def main():
    setup_folder_structure()

    folder = "validate"

    max_ = 100
    for i in range(0, max_):
        print(f"Generating {i+1}/{max_}")
        generate_random_scene(
            f"{i}", 
            project_folder + f"model-data\\{folder}\\images\\", 
            project_folder + f"model-data\\{folder}\\labels\\", 
            scale=3, 
            resolution=.4
        )

main()