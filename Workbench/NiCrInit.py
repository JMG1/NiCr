# -*- coding: utf-8 -*-
# NiCr (Hot Wire CNC Cutter) workbench for FreeCAD
# (c) 2016 Javier Martínez García
#***************************************************************************
#*   (c) Javier Martínez García 2016                                       *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License (GPL)            *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************/

import os
import FreeCAD
import FreeCADGui
import NiCrSimMachine as NiCrSM
import NiCrPath

__dir__ = os.path.dirname(__file__)


class CreateNiCrMachine:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/CreateMachine.svg',
                'MenuText': 'Add Simulation Machine',
                'ToolTip': 'Places one NiCr machine in the active document'}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            try:
                a=FreeCAD.ActiveDocument.NiCrMachine.Name
                return False
            except:
                return True

    def Activated(self):
        # check for already existing machines:
        m_created = False
        if FreeCAD.ActiveDocument.getObject('NiCrMachine'):
            # yes, this is stupid
            m_created = True

        if not(m_created):
            # workaround
            m = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroupPython', 'NiCrMachine')
            NiCrSM.NiCrMachine(m)
            NiCrSM.NiCrMachineViewProvider(m.ViewObject)
            FreeCAD.Gui.SendMsgToActiveView('ViewFit')
            FreeCAD.ActiveDocument.recompute()


class CreateToolPath:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/WirePath.svg',
                'MenuText': 'Route',
                'ToolTip': 'Create the wirepaths for the selected objects'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.NiCrMachine
            return True

        except:
            return False


    def Activated(self):
        # retrieve Selection
        selection = FreeCAD.Gui.Selection.getSelectionEx()
        for i in range(len(selection)):
            # create WirePath folder if it does not exist
            try:
                WPFolder = FreeCAD.ActiveDocument.WirePath

            except:
                WPFolder = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroupPython', 'WirePath')
                NiCrPath.WirePathFolder(WPFolder)

            # create shapepath object
            selObj = selection[i].Object
            shapepath_name = 'ShapePath_' + selObj.Name
            shapepathobj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', shapepath_name)
            # initialize python object
            NiCrPath.ShapePath(shapepathobj, selObj)
            NiCrPath.ShapePathViewProvider(shapepathobj.ViewObject)
            # modify color
            shapepathobj.ViewObject.ShapeColor = (1.0, 1.0, 1.0)
            shapepathobj.ViewObject.LineWidth = 1.0
            WPFolder.addObject(shapepathobj)



class CreatePathLink:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/PathLink.svg',
                'MenuText': 'Link Path',
                'ToolTip': 'Create a link between selected paths'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.NiCrMachine
            return True

        except:
            return False


    def Activated(self):
        # retrieve selection
        selection = FreeCAD.Gui.Selection.getSelectionEx()
        if len(selection) == 1:
            # Create initial/end path if length of selection == 1
            selObj = selection[0]
            try:
                a = FreeCAD.ActiveDocument.InitialPath
                try:
                    a = FreeCAD.ActiveDocument.FinalPath

                except:
                    # create final path, because initial path already exists
                    finalobj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython','FinalPath')
                    NiCrPath.FinalPath(finalobj, selObj)
                    NiCrPath.FinalPathViewProvider(finalobj.ViewObject)
                    finalobj.ViewObject.ShapeColor = (1.0, 1.0, 1.0)
                    finalobj.ViewObject.Transparency = 15
                    finalobj.ViewObject.DisplayMode = 'Shaded'
                    FreeCAD.ActiveDocument.WirePath.addObject(finalobj)

            except:
                # create initial path object
                initialobj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython','InitialPath')
                NiCrPath.InitialPath(initialobj, selObj)
                NiCrPath.InitialPathViewProvider(initialobj.ViewObject)
                # initial trajectory is red
                initialobj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
                initialobj.ViewObject.Transparency = 15
                initialobj.ViewObject.DisplayMode = 'Shaded'
                FreeCAD.ActiveDocument.WirePath.addObject(initialobj)

        if len(selection) == 2:
            # Create link between paths if len(selection) = 2
            selA = selection[0]
            selB = selection[1]
            SelObjA = selA.Object
            SelObjB = selA.Object
            # Link object
            link_name = 'Link_' + SelObjA.Name[8:] + '_' + SelObjB.Name[8:]
            LinkObj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', link_name)
            # initialize link object
            NiCrPath.LinkPath(LinkObj, selA, selB)
            NiCrPath.LinkPathViewProvider(LinkObj.ViewObject)
            # link representation
            # LinkObj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
            LinkObj.ViewObject.Transparency = 15
            # LinkObj.ViewObject.LineColor = (1.0, 0.0, 0.0)
            LinkObj.ViewObject.DisplayMode = "Shaded"
            # add to folder
            FreeCAD.ActiveDocument.WirePath.addObject(LinkObj)


class SaveWirePath:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/SavePath.svg',
                'MenuText': 'Save Path',
                'ToolTip': 'Exports current wirepath to a .nicr file'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.FinalPath
            return True
        except:
            return False

    def Activated(self):
        NiCrPath.saveNiCrFile()


class ImportWirePath:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/SavePath.svg',
                'MenuText': 'Import WirePath',
                'ToolTip': 'Exports current wirepath to a .nicr file'}

    def IsActive(self):
        return True

    def Activated(self):
        NiCrPath.importNiCrFile()

# Animation classes
class RunPathSimulation:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AnimateMachine.svg',
                'MenuText': 'Start Animation',
                'ToolTip': 'Start animation of the current toolpath'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.FinalPath
            return True
        except:
            return False

    def Activated(self):
        full_path = NiCrPath.CreateCompleteRawPath()
        NiCrSM.runSimulation(full_path)
        FreeCAD.Console.PrintMessage('Simulation finished\n')



if FreeCAD.GuiUp:
    FreeCAD.Gui.addCommand('CreateNiCrMachine', CreateNiCrMachine())
    FreeCAD.Gui.addCommand('CreateToolPath', CreateToolPath())
    FreeCAD.Gui.addCommand('CreatePathLink', CreatePathLink())
    FreeCAD.Gui.addCommand('SaveWirePath', SaveWirePath())
    FreeCAD.Gui.addCommand('ImportWirePath', ImportWirePath())
    FreeCAD.Gui.addCommand('RunPathSimulation', RunPathSimulation())
