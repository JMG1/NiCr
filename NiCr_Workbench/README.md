## NiCr: FreeCAD Workbench

This is a dedicated workbench to create and simulate toolpaths('wirepaths') for the NiCr machine using FreeCAD.
Version 0.1

### Command line installation on Ubuntu/Mint/similar:
Open one terminal window (usually **ctrl+alt+t** ) and copy-paste line by line:

**sudo apt-get install git**

**git clone https://github.com/JMG1/NiCr**

**cd ~/NiCr**

**mv NiCr_Workbench ~/.FreeCAD/Mod**

**cd ~/**

**rm -rf NiCr**

That's all.


### Windows/Manual install
Download the repository (https://github.com/JMG1/NiCr) as ZIP file and extract the folder 'NiCr_Workbench' 
inside **C:\Program Files\FreeCAD\Mod** for Windows or /usr/lib/FreeCAD/Mod for Debian-like systems.

### What to do then?

Check the file NiCrExample.fcstd that is inside the workbench. It contains an example of wirepath, links between 
paths and more.



