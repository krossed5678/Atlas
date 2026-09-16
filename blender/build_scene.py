import bpy, json, sys
from pathlib import Path

out=Path(sys.argv[-1]); out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(location=(0,0,1.5)); room=bpy.context.object; room.name='ROOM_SHELL_PLACEHOLDER'; room.scale=(3,3,1.5)
bpy.ops.object.camera_add(location=(0,-6,1.6)); camera=bpy.context.object; bpy.context.scene.camera=camera
bpy.ops.object.light_add(type='AREA', location=(0,-2,3)); bpy.context.object.data.energy=800
bpy.context.scene.render.engine='BLENDER_EEVEE'; bpy.context.scene.render.resolution_x=768; bpy.context.scene.render.resolution_y=512; bpy.context.scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(out))
