# blender-numpy-depth-map-importer
Import .npy and .npz depth map files into Blender as meshes.

## Installation:
1. Download `blender_npy_depth_import.py`.
2. Open Blender, select Preferences from the Edit menu.
3. Click the "Get Extensions" tab.
4. Click the menu dropdown arrow in the top right corner of the preferences window, select "Install from Disk...".
5. Select the `blender_npy_depth_import.py` file.

## Use:
This extension adds a "NPY Depth Map (.npy, .npz)" option under File->Import. Select the option and choose a valid depth map file.  By default, depth maps are imported as planes, but in the file selection window you can click "Use Cube" to instead import it as a solid volume for easier use with 3D printing. Note that if you're using a .npz file, the extension expects that the first array packaged within it will be the depth map.
