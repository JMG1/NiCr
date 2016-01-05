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
import Part
import NiCrSimMachine as NiCrSM
import NiCrPath as NiCrPth

__dir__ = os.path.dirname(__file__)

class CreateSimMachine:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/CreateMachine.svg',
                'MenuText': 'Add Simulation Machine',
                'ToolTip': 'Places one NiCr machine in the active document'}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            try:
                a=FreeCAD.ActiveDocument.SimMachine.Name
                return False
            except:
                return True

    def Activated(self):
        # check for already existing machines:
        m_created = False
        if FreeCAD.ActiveDocument.getObject('SimMachine'):
            # yes, this is stupid
            m_created = True

        if not(m_created):
            # workaround
            m = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', 'NiCrMachine')
            FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroup', 'SimMachine')
            NiCrSM.SimMachine(m)
            NiCrSM.SimMachineViewProvider(m.ViewObject)
            FreeCAD.Gui.SendMsgToActiveView('ViewFit')
            FreeCAD.ActiveDocument.recompute()


class CreateToolPath:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/RoutePart.svg',
                'MenuText': 'Route',
                'ToolTip': 'Create the wirepaths for the selected objects'}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True

    def Activated(self):
        # create wirepath object
        for i in range(len(FreeCAD.Gui.Selection.getSelectionEx())):
            selObj = FreeCAD.Gui.Selection.getSelectionEx()[i].Object
            wirepath_name = 'Wirepath_' + selObj.Name
            wirepathobj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', wirepath_name)
            NiCrPth.WirePath(wirepathobj, selObj)
            NiCrPth.WirePathViewProvider(wirepathobj.ViewObject)
            # wirepathobj.ViewObject.DisplayMode = "Shaded"
            wirepathobj.ViewObject.DisplayMode = 'Flat Lines'
            wirepathobj.ViewObject.LineWidth = 1.00
            wirepathobj.ViewObject.ShapeColor = (0.00, 1.00, 1.00)
            # wirepathobj.ViewObject.LineColor = (1.00, 0.67, 0.00)
            # create CompleteWirePath if none exists
            try:
                cmplWP = FreeCAD.ActiveDocument.Wirepath

            except:
                cmplWP = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroupPython', 'Wirepath')
                NiCrPth.WirePathFolder(cmplWP)

            # update cut order
            # place inside complete wire path folder
            cmplWP.addObject(wirepathobj)


class CreatePathLink:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/PathLink.svg',
                'MenuText': 'Link Path',
                'ToolTip': 'Create a link between selected paths'}

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True

    def Activated(self):
        # Selection
        SelObjA = FreeCAD.Gui.Selection.getSelectionEx()[0].Object
        SelObjB = FreeCAD.Gui.Selection.getSelectionEx()[1].Object
        # Link object
        link_name = 'Link_' + SelObjA.Name[8:] + '_' + SelObjB.Name[8:]
        LinkObj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', link_name)
        # initialize link object
        NiCrPth.LinkPath(LinkObj)
        NiCrPth.LinkPathViewObject(LinkObj.ViewObject)
        # link representation
        LinkObj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
        LinkObj.ViewObject.Transparency = 15
        # LinkObj.ViewObject.LineColor = (1.0, 0.0, 0.0)
        LinkObj.ViewObject.DisplayMode = "Shaded"
        # folder and schedule
        cmplWP = FreeCAD.ActiveDocument.Wirepath
        cmplWP.ShapeSequence.append(LinkObj.Name)
        cmplWP.addObject(LinkObj)

class CreateZeroLink:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/ZeroPath.svg',
                'MenuText': 'Zero Link',
                'ToolTip': 'Creates link path between machine zero and selected point'}

    def IsActive(self):
        try:
            a = FreeCAD.Gui.Selection.getSelectionEx()[0]
            return True
        except:
            return False

    def Activated(self):
        zeroLinkObj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', 'ZeroLink')
        NiCrPth.LinkZero(zeroLinkObj)
        NiCrPth.LinkZeroViewProvider(zeroLinkObj.ViewObject)
        zeroLinkObj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
        zeroLinkObj.ViewObject.Transparency = 15
        zeroLinkObj.ViewObject.DisplayMode = 'Shaded'
        cmplWP = FreeCAD.ActiveDocument.Wirepath
        cmplWP.addObject(zeroLinkObj)


class SaveToolPath:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/SavePath.svg',
                'MenuText': 'Save Path',
                'ToolTip': 'Exports current wirepath to a .nicr file'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.Wirepath.ShapeSequence[0]
            return True
        except:
            return False

    def Activated(self):
        NiCrPth.saveNiCrFile()

# Animation classes
class RunPathSimulation:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AnimateMachine.svg',
                'MenuText': 'Start Animation',
                'ToolTip': 'Start animation of the current toolpath'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.Wirepath.ShapeSequence[0]
            return True
        except:
            return False

    def Activated(self):
        full_path = NiCrPth.createFullPath()
        NiCrPth.runSimulation(full_path)
        FreeCAD.Console.PrintMessage('Simulation finished\n')



if FreeCAD.GuiUp:
    FreeCAD.Gui.addCommand('CreateSimMachine', CreateSimMachine())
    FreeCAD.Gui.addCommand('CreateToolPath', CreateToolPath())
    FreeCAD.Gui.addCommand('CreatePathLink', CreatePathLink())
    FreeCAD.Gui.addCommand('SaveToolPath', SaveToolPath())
    FreeCAD.Gui.addCommand('RunPathSimulation', RunPathSimulation())
    FreeCAD.Gui.addCommand('CreateZeroLink', CreateZeroLink())
