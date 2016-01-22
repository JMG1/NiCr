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
import FreeCAD
import FreeCADGui


class NiCrWorkbench(Workbench):
    import NiCrInit  # this is needed to load the workbench icon
    # __dir__ = os.path.dirname( __file__ ) # __file__ is not working
    Icon = NiCrInit.__dir__ + '/icons/WorkbenchIcon.svg'
    MenuText = 'NiCr'
    ToolTip = 'Workbench for the NiCr foam cutter machine'

    def GetClassName(self):
        return 'Gui::PythonWorkbench'

    def Initialize(self):
        import NiCrInit
        self.tools = ['CreateSimMachine',
                      'CreateToolPath',
                      'CreatePathLink',
                      'SaveWirePath',
                      'ImportWirePath',
                      'RunPathSimulation']

        FreeCAD.t = self.appendToolbar('NiCrWorkbench', self.tools)
        self.appendMenu('NiCrWorkbench', self.tools)
        FreeCAD.Console.PrintMessage('NiCr workbench loaded\n')

    def Activated(self):
        pass


FreeCADGui.addWorkbench(NiCrWorkbench)
