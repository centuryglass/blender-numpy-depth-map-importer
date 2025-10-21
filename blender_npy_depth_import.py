bl_info = {
    "name": "NPY Depth Map Importer",
    "author": "Anthony Brown",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "File > Import",
    "description": "Import .npy/.npz depth maps as meshes",
    "category": "Import-Export",
}

import bpy
import bmesh
import numpy as np
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty
from mathutils import Vector

class ImportNPYDepthMap(bpy.types.Operator, ImportHelper):
    """Import NPY/NPZ depth map as mesh"""
    bl_idname = "import_mesh.npy_depth"
    bl_label = "Import NPY Depth Map"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".npy;.npz"
    
    filter_glob: StringProperty(
        default="*.npy;*.npz",
        options={'HIDDEN'},
    )
    
    use_cube: BoolProperty(
        name="Use Cube (instead of Plane)",
        description="Create a cube mesh instead of plane",
        default=False,
    )
    
    depth_scale: FloatProperty(
        name="Depth Scale",
        description="Scale factor for depth values",
        default=1.0,
        min=0.001,
        max=1000.0,
    )
    
    def execute(self, context):
        try:
            # Load the numpy data
            data = np.load(self.filepath)
            
            if isinstance(data, np.lib.npyio.NpzFile):
                # For .npz files, use the first array
                array_key = data.files[0]
                depth_array = data[array_key]
            else:
                depth_array = data
            
            # Ensure it's 2D
            if depth_array.ndim != 2:
                self.report({'ERROR'}, "Depth map must be 2D")
                return {'CANCELLED'}
            
            # Normalize and process the depth data
            depth_array = self.process_depth_array(depth_array)
            
            # Create mesh
            if self.use_cube:
                mesh_obj = self.create_cube_mesh(depth_array, context)
            else:
                mesh_obj = self.create_plane_mesh(depth_array, context)
            
            # Select and make active
            bpy.ops.object.select_all(action='DESELECT')
            mesh_obj.select_set(True)
            context.view_layer.objects.active = mesh_obj
            
            self.report({'INFO'}, f"Successfully imported {mesh_obj.name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import: {str(e)}")
            return {'CANCELLED'}
    
    def process_depth_array(self, depth_array):
        """Process and normalize depth array"""
        # Remove any NaN/inf values
        depth_array = np.nan_to_num(depth_array)
        
        # Normalize to 0-1 range and apply scale
        depth_min = np.min(depth_array)
        depth_max = np.max(depth_array)
        
        if depth_max - depth_min > 0:
            depth_array = (depth_array - depth_min) / (depth_max - depth_min)
        
        depth_array *= self.depth_scale
        

        return depth_array
    
    def create_depthmap_bmesh(self, depth_array):
        """Add faces and vertices from a depth array to a new blender bmesh."""
        height, width = depth_array.shape
        # Create bmesh
        mesh = bmesh.new()
        mesh_width = 1.0
        mesh_height = 1.0
        if width > height:
            mesh_height = height / width
        elif height > width:
            mesh_width = width / height
            
        # Create vertices
        for y in range(height):
            for x in range(width):
                # Normalize coordinates:
                x_norm = x / (width - 1) * mesh_width if width > 1 else 0
                y_norm = y / (height - 1) * mesh_height if height > 1 else 0
                
                # Get depth value (invert Y for Blender coordinate system)
                z = depth_array[height - 1 - y, x]
                
                # Create vertex
                mesh.verts.new((x_norm - 0.5, y_norm - 0.5, z))
        
        mesh.verts.ensure_lookup_table()
        
        # Create faces (quads)
        for y in range(height - 1):
            for x in range(width - 1):
                v1 = y * width + x
                v2 = y * width + (x + 1)
                v3 = (y + 1) * width + (x + 1)
                v4 = (y + 1) * width + x
                
                try:
                    mesh.faces.new([mesh.verts[v1], mesh.verts[v2], mesh.verts[v3], mesh.verts[v4]])
                except:
                    # Face might already exist or be degenerate
                    pass
        return mesh
    
    def create_plane_mesh(self, depth_array, context):
        """Create mesh directly from depth map (more efficient)"""
        
        # Create mesh and object
        mesh = bpy.data.meshes.new("DepthMap_Plane")
        obj = bpy.data.objects.new("DepthMap_Plane", mesh)
        
        # Link to scene
        context.collection.objects.link(obj)
        
        # Create bmesh
        bm = self.create_depthmap_bmesh(depth_array)
        
        # Update mesh
        bm.to_mesh(mesh)
        bm.free()
        
        return obj
    
    def create_cube_mesh(self, depth_array, context):
        """Add a border and base to the mesh plane (better for 3D printing)"""
        
        # pad with new max depth values for the base:
        base_z = np.max(depth_array)
        depth_array = np.pad(depth_array, pad_width=1, mode='constant', constant_values=base_z)
        
        
        mesh = bpy.data.meshes.new("DepthMap_Cube")
        obj = bpy.data.objects.new("DepthMap_Cube", mesh)
        
        # Link to scene:
        context.collection.objects.link(obj)
        
        bm = self.create_depthmap_bmesh(depth_array)
        
        # Add base face:
        height, width = depth_array.shape
        base_verts = []
        
        for y in range(height - 1):
            base_verts.append(bm.verts[y * width])
        for x in range(1, width - 1):
            base_verts.append(bm.verts[(height - 1) * width + x])
        for y in reversed(range(height - 2)):
            base_verts.append(bm.verts[y * width + (width - 1)])
        for x in reversed(range(1, width - 2)):
            base_verts.append(bm.verts[x])
        try:
            bm.faces.new(base_verts)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create base face: {str(e)}")

        # Update mesh
        bm.to_mesh(mesh)
        bm.free()
        
        return obj

def menu_func_import(self, context):
    self.layout.operator(ImportNPYDepthMap.bl_idname, text="NPY Depth Map (.npy, .npz)")

def register():
    bpy.utils.register_class(ImportNPYDepthMap)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportNPYDepthMap)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
