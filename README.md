# VMDL_C Converter
### Purpose
This program was developed to allow easier clipping of prop ramps for CS2 porting. This program allows .vmdl_c files to be converted to obj files, and in the process will merge triangular faces (coplanar faces). These models can then be easily imported using file->import into hammer directly, and then the faces can be used to clip prop ramps very easily.

### Requirements
This program uses the CLI version of Source2Viewer to decompile the .vmdl_c files, and thus can only be run on windows.
It is entirely CPU based, it does not require any raytracing and thus has no GPU requirements.
Currently the program handles the front end and all of the model processing synchronously so there may be a non-responding period during processing. The program will be updated to handle processing asynchronously at a later release.

### How To Use
1. Find your base game directory (e.g. "F:/Program Files (x86)/Steam/steamapps/common/Counter-Strike Global Offensive")
2. Select your output directory (Where you want the obj files to be placed)
3. Select an addon from the list, and click extract models.
4. Select which models you want to convert to obj
5. Adjust the threshold for the de-triangularisation algorithm
6. Select which files you want to construct (From Physics only, from Render only or from both combined)
7. Click "Convert Models"

## It will convert ramps like this:

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/before.png)

## Into ramps like this:

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/after.png)
