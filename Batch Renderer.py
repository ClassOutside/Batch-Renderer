import bpy
import os

bl_info = {
    "name": "Batch Renderer",
    "author": "ClassOutside",
    "version": (1, 0),
    "blender": (4, 1, 1),
    "description": "Assists with rendering multiple image sequences in Blender",
}

class CustomPathItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Path")

class CustomContextMenuOperator(bpy.types.Operator):
    bl_idname = "sequencer.custom_context_menu"
    bl_label = "Start Batch Render"
    
    def execute(self, context):
        selected_paths = context.window_manager.custom_selected_paths
        selected_paths.clear()

        for file in context.selected_files:
            if hasattr(file, "name"):
                full_path = os.path.join(context.space_data.params.directory.decode('utf-8'), file.name)
                if os.path.isdir(full_path):
                    item = selected_paths.add()
                    item.name = full_path

        bpy.ops.wm.custom_dialog_operator('INVOKE_DEFAULT')

        return {'FINISHED'}


class CustomDialogOperator(bpy.types.Operator):
    bl_idname = "wm.custom_dialog_operator"
    bl_label = "Selected Folders"

    frame_rate: bpy.props.EnumProperty(
        name="Frame Rate",
        items=[
            ('24', "24 FPS", ""),
            ('30', "30 FPS", ""),
            ('60', "60 FPS", "")
        ],
        default='24'
    )

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        row = layout.row()
        row.template_list("Custom_UL_items", "", wm, "custom_selected_paths", wm, "custom_selected_path_index")

        row = layout.row()
        row.operator("wm.custom_add_folder", text="Add Folder")
        row.operator("wm.custom_remove_folder", text="Remove Folder")

        row = layout.row()
        row.prop(self, "frame_rate")

    def execute(self, context):
        wm = context.window_manager
        frame_rate = int(self.frame_rate)

        for item in wm.custom_selected_paths:
            folder_path = item.name
            folder_name = os.path.basename(folder_path)
            
            image_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            if not image_files:
                print(f"No image files found in {folder_path}")
                continue

            for area in bpy.context.screen.areas:
                if area.type == 'SEQUENCE_EDITOR':
                    with bpy.context.temp_override(area=area):
                        bpy.ops.sequencer.select_all(action='SELECT')
                        bpy.ops.sequencer.delete()
                        
                        bpy.ops.sequencer.image_strip_add(
                            directory=folder_path,
                            files=[{"name": f} for f in image_files],
                            frame_start=1
                        )
                        
                        num_images = len(image_files)
                        print(f"Added {num_images} images from {folder_path}")

                        scene = bpy.context.scene
                        scene.frame_end = num_images
                        scene.render.fps = frame_rate
                        scene.render.image_settings.file_format = 'FFMPEG'
                        scene.render.ffmpeg.format = 'MPEG4'
                        scene.render.ffmpeg.codec = 'H264'
                        scene.render.ffmpeg.constant_rate_factor = 'HIGH'
                        scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
                        output_path = os.path.join(os.path.dirname(folder_path), folder_name)
                        scene.render.filepath = output_path

                        print(f"Rendering animation to {output_path}")
                        bpy.ops.render.render(animation=True)
                    break
        
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

class CustomAddFolderOperator(bpy.types.Operator):
    bl_idname = "wm.custom_add_folder"
    bl_label = "Add Folder"

    def execute(self, context):
        context.window_manager.custom_selected_paths.add().name = "New Folder"
        return {'FINISHED'}

class CustomRemoveFolderOperator(bpy.types.Operator):
    bl_idname = "wm.custom_remove_folder"
    bl_label = "Remove Folder"

    def execute(self, context):
        wm = context.window_manager
        if wm.custom_selected_paths and wm.custom_selected_path_index < len(wm.custom_selected_paths):
            wm.custom_selected_paths.remove(wm.custom_selected_path_index)
        return {'FINISHED'}

class Custom_UL_items(bpy.types.UIList):
    pass

def menu_func(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("sequencer.custom_context_menu")

def register():
    bpy.utils.register_class(CustomPathItem)
    bpy.utils.register_class(CustomContextMenuOperator)
    bpy.utils.register_class(CustomDialogOperator)
    bpy.utils.register_class(CustomAddFolderOperator)
    bpy.utils.register_class(CustomRemoveFolderOperator)
    bpy.utils.register_class(Custom_UL_items)
    bpy.types.FILEBROWSER_MT_context_menu.append(menu_func)
    bpy.types.WindowManager.custom_selected_paths = bpy.props.CollectionProperty(type=CustomPathItem)
    bpy.types.WindowManager.custom_selected_path_index = bpy.props.IntProperty()

def unregister():
    bpy.utils.unregister_class(CustomPathItem)
    bpy.utils.unregister_class(CustomContextMenuOperator)
    bpy.utils.unregister_class(CustomDialogOperator)
    bpy.utils.unregister_class(CustomAddFolderOperator)
    bpy.utils.unregister_class(CustomRemoveFolderOperator)
    bpy.utils.unregister_class(Custom_UL_items)
    bpy.types.FILEBROWSER_MT_context_menu.remove(menu_func)
    del bpy.types.WindowManager.custom_selected_paths
    del bpy.types.WindowManager.custom_selected_path_index

if __name__ == "__main__":
    register()
