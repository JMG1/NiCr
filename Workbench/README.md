## NiCr: FreeCAD Workbench

This is a dedicated FreeCAD workbench to create and simulate toolpaths('wirepaths') for the NiCr machine.


### Details:
  #### Things that work (but are not finished):
  - Parametric machine
  - Shape to wirepath algorithm
  - Links between wirepaths
  - Wirepath animation
  

  #### Things only accesible by code:
  - Wirepath to .nicr exporter



### Command line installation in Ubuntu/Mint/similar:
  Open one terminal window (usually **ctrl+alt+t** ) and copy-paste line by line:
  
  **sudo apt-get install git**
  
  **git clone https://github.com/JMG1/NiCr**
  
  **cd ~/NiCr**
  
  **mv Workbench ~/.FreeCAD/Mod**
  
  **cd ~/**
  
  **rm -rf NiCr**
  
  That's all.


### Windows/Manual install (available to all users)
  Download the repository (https://github.com/JMG1/NiCr) as ZIP file and extract the folder 'Workbench' 
  inside **C:\Program Files\FreeCAD\Mod** for Windows or **/usr/lib/FreeCAD/Mod** for Debian-like systems.

### What to do now?
  Check the file NiCrExample.fcstd that is inside the workbench. It contains an example of wirepath, links between 
  paths and more.
  


