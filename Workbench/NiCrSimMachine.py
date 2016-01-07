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
import Part

class SimMachine:
    def __init__( self, obj ):
        # geometric properties
        obj.addProperty( 'App::PropertyFloat',
                         'XLength',
                         'Machine Geometry' ).XLength = 800.0

        obj.addProperty( 'App::PropertyFloat',
                         'YLength',
                         'Machine Geometry' ).YLength = 600.0

        obj.addProperty( 'App::PropertyFloat',
                         'ZLength',
                         'Machine Geometry' ).ZLength = 800.0

        obj.addProperty( 'App::PropertyFloat',
                         'FrameDiameter',
                         'Machine Geometry' ).FrameDiameter = 30.0

        obj.addProperty('App::PropertyVector',
                        'VirtualMachineZero').VirtualMachineZero = FreeCAD.Vector(0, 0, 0)

        obj.Proxy = self
        self.addMachineToDocument( obj.FrameDiameter, obj.XLength, obj.YLength, obj.ZLength, created=False )
        obj.VirtualMachineZero = FreeCAD.Vector(obj.FrameDiameter*1.6, obj.FrameDiameter*1.8, 0)


    def onChanged( self, fp, prop):
        try:
            if prop == 'XLength' or prop == 'YLength' or prop == 'ZLength' or prop == 'FrameDiameter':
                self.addMachineToDocument( fp.FrameDiameter, fp.XLength, fp.YLength, fp.ZLength )

        except AttributeError:
            pass


    def execute( self, fp ):
        pass

    def buildMachine( self, tube_diameter, w_x, w_y, w_z ):
        main_cube = Part.makeBox( w_x + 2*tube_diameter,
                                  w_y + 2*tube_diameter,
                                  w_z + 2*tube_diameter,
                                  FreeCAD.Vector(-1.6*tube_diameter,
                                                 -1.8*tube_diameter,
                                                 -1.1*tube_diameter))

        xy_cutcube = Part.makeBox( w_x,
                                   w_y,
                                   w_z*1.5,
                                   FreeCAD.Vector(-0.6*tube_diameter,
                                                  -0.8*tube_diameter,
                                                  -2.1*tube_diameter))
        xz_cutcube = Part.makeBox( w_x,
                                   w_y*1.5,
                                   w_z,
                                   FreeCAD.Vector( -0.6*tube_diameter,
                                                   -2.8*tube_diameter,
                                                   -0.1*tube_diameter))

        yz_cutcube = Part.makeBox( w_x*1.5,
                                   w_y,
                                   w_z,
                                   FreeCAD.Vector( -2.6*tube_diameter,
                                                   -0.8*tube_diameter,
                                                   -0.1*tube_diameter ) )

        frame = main_cube.cut( xy_cutcube )
        frame = frame.cut( xz_cutcube )
        frame = frame.cut( yz_cutcube )
        # machine x axis frame
        xa_frame = Part.makeBox( tube_diameter,
                                 w_y,
                                 tube_diameter,
                                 FreeCAD.Vector( -0.5*tube_diameter,
                                                 -0.8*tube_diameter,
                                                 -1.1*tube_diameter))

        xb_frame = Part.makeBox( tube_diameter,
                                 w_y,
                                 tube_diameter,
                                 FreeCAD.Vector( -0.5*tube_diameter,
                                                 -0.8*tube_diameter,
                                                 w_z + -0.1*tube_diameter))

        # machine y axis frame
        ya_frame = Part.makeBox( tube_diameter*1.2,
                                 tube_diameter*1.6,
                                 tube_diameter*1.2,
                                 FreeCAD.Vector( -0.6*tube_diameter,
                                                 -0.8*tube_diameter,
                                                 -1.2*tube_diameter))

        yb_frame = Part.makeBox( tube_diameter*1.2,
                                 tube_diameter*1.6,
                                 tube_diameter*1.2,
                                 FreeCAD.Vector( -0.6*tube_diameter,
                                                 -0.8*tube_diameter,
                                                 w_z - tube_diameter*0.2 ) )
        #dbm('2.3')
        return frame, xa_frame, xb_frame, ya_frame, yb_frame

    def addMachineToDocument(self, FrameDiameter, XLength, YLength, ZLength, created=True):
        # temporal workarround until:http://forum.freecadweb.org/viewtopic.php?f=22&t=13337
        #dbm( '0' )
        mfolder = FreeCAD.ActiveDocument.getObject('SimMachine')
        #dbm( '1' )
        # Remove previous machine parts
        if created:
            FreeCAD.ActiveDocument.removeObject('Frame')
            FreeCAD.ActiveDocument.removeObject('XA')
            FreeCAD.ActiveDocument.removeObject('XB')
            FreeCAD.ActiveDocument.removeObject('YA')
            FreeCAD.ActiveDocument.removeObject('YB')

        # machine shapes
        machine_shapes = self.buildMachine(FrameDiameter,
                                           XLength,
                                           YLength,
                                           ZLength)
        # temporal workaround
        #mfolder = FreeCAD.ActiveDocument.addObject( 'App::DocumentObjectGroup','SimMachine' )
        obj_frame = FreeCAD.ActiveDocument.addObject('Part::Feature', 'Frame')
        obj_XA = FreeCAD.ActiveDocument.addObject('Part::Feature', 'XA')
        obj_XB = FreeCAD.ActiveDocument.addObject('Part::Feature', 'XB')
        obj_YA = FreeCAD.ActiveDocument.addObject('Part::Feature', 'YA')
        obj_YB = FreeCAD.ActiveDocument.addObject('Part::Feature', 'YB')
        obj_frame.Shape = machine_shapes[0]
        obj_XA.Shape = machine_shapes[1]
        obj_XB.Shape = machine_shapes[2]
        obj_YA.Shape = machine_shapes[3]
        obj_YB.Shape = machine_shapes[4]
        obj_frame.ViewObject.ShapeColor = (0.67, 0.78, 0.85)
        obj_XA.ViewObject.ShapeColor = (0.00, 0.67, 1.00)
        obj_XB.ViewObject.ShapeColor = (0.00, 0.67, 1.00)
        obj_YA.ViewObject.ShapeColor = (0.00, 1.00, 0.00)
        obj_YB.ViewObject.ShapeColor = (0.00, 1.00, 0.00)
        obj_frame.ViewObject.Selectable = False
        obj_XA.ViewObject.Selectable = False
        obj_XB.ViewObject.Selectable = False
        obj_YA.ViewObject.Selectable = False
        obj_YB.ViewObject.Selectable = False
        mfolder.addObject(obj_frame)
        mfolder.addObject(obj_XA)
        mfolder.addObject(obj_XB)
        mfolder.addObject(obj_YA)
        mfolder.addObject(obj_YB)


class SimMachineViewProvider:
    def __init__(self, obj):
        obj.Proxy = self

    def getDefaultDisplayMode(self):
        return "Flat Lines"

    def getIcon(self):
        import os
        __dir__ = os.path.dirname(__file__)
        return __dir__ + '/icons/CreateMachine.svg'

def dbm(ms):
    # debug messages
    FreeCAD.Console.PrintMessage( '\n' + ms + '\n' )
