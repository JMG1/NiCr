## NiCr: FreeCAD Workbench

This is a dedicated FreeCAD workbench to create and simulate toolpaths('wirepaths') for the NiCr machine.
At the moment it is in heavy development.

####Workbench demo videos:

DevUpdate 1 (current): https://www.youtube.com/watch?v=IMD8KxX-TPg

DevUpdate 0: https://www.youtube.com/watch?v=8snH_p_onoQ


### Current Features*:
  - Parametric machine
  - Shape to wirepath algorithm
  - Links between wirepaths
  - Save wirepath as .nicr (GCode-like) file
  - Wirepath animation

  *some functionalities are not complete.

### Command line installation in Ubuntu/Mint/similar:
  Open one terminal window (usually **ctrl+alt+t** ) and copy-paste line by line:
  
  Install git:
  **sudo apt-get install git**
  
  Clone repository:
  **git clone https://github.com/JMG1/NiCr**
  
  Move workbench folder to /.FreeCAD/Mod:
  **mv ~/NiCr/Workbench ~/.FreeCAD/Mod**
  
  Remove the NiCr folder (if you only want the workbench)
  **rm -rf NiCr**
  
  That's all.


### Windows/Manual install (available to all users)
  Download the repository (https://github.com/JMG1/NiCr) as ZIP file and extract the folder 'Workbench' 
  inside **C:\Program Files\FreeCAD\Mod** for Windows or **/usr/lib/FreeCAD/Mod** for Debian-like systems.

### What to do now?
  Check the file NiCrExample.fcstd that is inside the workbench. It contains an example of wirepath, links between 
  paths and more.
  


