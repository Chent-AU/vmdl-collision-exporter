# VMDL_C Converter

## Contents
- [Purpose](#purpose)
- [Requirements](#requirements)
- [Guide](#guide)

### Purpose
This program was developed to allow easier clipping of prop ramps for CS2 porting. This program allows .vmdl_c files to be converted to obj files, and in the process will merge triangular faces (coplanar faces). These models can then be easily imported using file->import into hammer directly, and then the faces can be used to clip prop ramps very easily.

#### It will convert ramps like this:

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/before.png)

#### Into ramps like this:

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/after.png)

### Requirements
This program uses the CLI version of Source2Viewer to decompile the .vmdl_c files, and thus can only be run on windows.
It is entirely CPU based, it does not require any raytracing and thus has no GPU requirements.

### Guide
1. Find your base game directory (e.g. "F:/Program Files (x86)/Steam/steamapps/common/Counter-Strike Global Offensive")

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-1.PNG)

3. Select your output directory (Where you want the obj files to be placed)

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-2.PNG)

5. Select an addon from the list, and click extract models.

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-3.PNG)

6. Select which models you want to convert to obj

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-4.PNG)
   
8. Adjust your export settings.
   - A vmdl may be made up of 2 parts, a physics hull for calculating collisions, and a render hull for appearance, or it may just have a single hull that does both. Typically you will want to export the physics hull for the purpose of clipping, but sometimes the physics hull may not include the entire ramp, or may be missing segments, in which case the combined model can be very useful, but beware it may sometimes have duplicate faces (identical faces on top of one another). The program will attempt to remove these duplicate faces, but if they are slightly misaligned then it will be unable to do so.
   - You may select to snap the verticies of the model to a grid size, this can help in removing duplicate faces.
   - The coplanar angle threshhold adjusts how similar two triangular faces have to be to be merged, typically 0.99 is fine, if you export your model and notice the faces are still triangular, try lowering this value.

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-5.PNG)

9. Click `Convert Models` and then import your model into hammer when they are completed via `File -> Import File`.

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-6.png)
  
11. Find the ramp prop entity you want to add the clip surface to, and copy the transform information to your clipboard.

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-7.png)
![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-8.png)

12. Then find your imported clip mesh, it will have no material and thus will be easy to spot. And paste the transform information.

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-9.png)
![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-10.png)

Your ramps should now be perfectly aligned like so:

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-11.png)

13. From here, you should select the faces you want to use as a clip, then use (in this order) `Detach Faces` *(N)* and then `Extract Faces` *(Alt + N)*, apply the `toolsplayerclip.vmat` material and then select the mesh of the other faces and delete them.

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-12.png)
![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-13.png)

14. Now you can delete any duplicate faces, and overlap the edges, thicken the faces and adjust the physics types as per the [CS2 Surf Mapping Guide](https://github.com/Chent-AU/CS2-Surf-Mapping) to complete the ramp clip.

![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-14.png)
![Alt text](https://raw.githubusercontent.com/Chent-AU/vmdl-collision-exporter/refs/heads/main/media/tute-15.png)

