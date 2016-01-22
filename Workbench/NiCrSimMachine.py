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

class NiCrMachine:
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

        obj.addProperty('App::PropertyFloat',
                        'FrameDiameter',
                        'Machine Geometry').FrameDiameter = 30.0

        obj.addProperty('App::PropertyVector',
                        'VirtualMachineZero',
                        'Machine Geometry').VirtualMachineZero = FreeCAD.Vector(0, 0, 0)

        obj.addProperty('App::PropertyBool',
                        'ReturnHome',
                        'Animation').ReturnHome = False

        obj.addProperty('App::PropertyBool',
                        'HideWireTrajectory',
                        'Animation').HideWireTrajectory = False

        obj.addProperty('App::PropertyBool',
                        'HideWire',
                        'Animation').HideWire = False

        obj.addProperty('App::PropertyFloat',
                        'AnimationDelay',
                        'Animation',
                        'Time between animation frames (0.0 = max speed)').AnimationDelay = 0.0

        obj.Proxy = self
        self.addMachineToDocument( obj.FrameDiameter, obj.XLength, obj.YLength, obj.ZLength, created=False )


    def onChanged(self, fp, prop):
        try:
            if prop == 'XLength' or prop == 'YLength' or prop == 'ZLength' or prop == 'FrameDiameter':
                self.addMachineToDocument( fp.FrameDiameter, fp.XLength, fp.YLength, fp.ZLength )

            if prop == 'ReturnHome' and fp.ReturnHome:
                # reset machine position
                homePlm = FreeCAD.Placement(FreeCAD.Vector(0,0,0),
                                            FreeCAD.Rotation(FreeCAD.Vector(0,0,0),0))
                FreeCAD.ActiveDocument.getObject('XA').Placement = homePlm
                FreeCAD.ActiveDocument.getObject('XB').Placement = homePlm
                FreeCAD.ActiveDocument.getObject('YA').Placement = homePlm
                FreeCAD.ActiveDocument.getObject('YB').Placement = homePlm
                fp.ReturnHome = False

            if prop == 'HideWireTrajectory':
                for obj in FreeCAD.ActiveDocument.WireTrajectory.Group:
                    obj.ViewObject.Visibility = fp.HideWireTrajectory

            if prop == 'HideWire':
                FreeCAD.ActiveDocument.Wire.ViewObject.Visibility = fp.HideWire

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
        mfolder = FreeCAD.ActiveDocument.getObject('NiCrMachine')
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
        #mfolder = FreeCAD.ActiveDocument.addObject( 'App::DocumentObjectGroup','NiCrMachine' )
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


class NiCrMachineViewProvider:
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


# Machine animation ----------------------------------------------------------
def runSimulation(complete_raw_path):
    # FreeCAD.ActiveDocument.WirePath.ViewObject.Visibility = False
    projected_trajectory_A = []
    projected_trajectory_B = []
    Z0 = FreeCAD.ActiveDocument.NiCrMachine.FrameDiameter*1.1*0
    ZL = FreeCAD.ActiveDocument.NiCrMachine.ZLength
    Z1 = ZL + Z0 - FreeCAD.ActiveDocument.NiCrMachine.FrameDiameter*0.2
    for i in range(len(complete_raw_path[0])):
        PA = complete_raw_path[0][i]
        PB = complete_raw_path[1][i]
        proj_A, proj_B = projectEdgeToTrajectory(PA, PB, Z0, Z1)
        projected_trajectory_A.append(proj_A)
        projected_trajectory_B.append(proj_B)

    machine_path = (projected_trajectory_A, projected_trajectory_B)

    # simulate machine path
    import time
    # create wire
    try:
        wire = FreeCAD.ActiveDocument.Wire
    except:
        wire = FreeCAD.ActiveDocument.addObject('Part::Feature', 'Wire')
        FreeCAD.ActiveDocument.NiCrMachine.addObject(wire)


    try:
        # remove previous trajectories
        for obj in FreeCAD.ActiveDocument.WireTrajectory.Group:
            FreeCAD.ActiveDocument.removeObject(obj.Name)

        FreeCAD.ActiveDocument.removeObject('WireTrajectory')

    except:
        pass

    wire_tr_folder = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroup', 'WireTrajectory')
    FreeCAD.ActiveDocument.NiCrMachine.addObject(wire_tr_folder)
    # retrieve machine shapes
    XA = FreeCAD.ActiveDocument.XA
    XB = FreeCAD.ActiveDocument.XB
    YA = FreeCAD.ActiveDocument.YA
    YB = FreeCAD.ActiveDocument.YB
    # ofsets
    xoff = FreeCAD.ActiveDocument.NiCrMachine.FrameDiameter*1.5*0
    yoff = FreeCAD.ActiveDocument.NiCrMachine.FrameDiameter*1.8*0
    wire_t_list = []
    animation_delay = FreeCAD.ActiveDocument.NiCrMachine.AnimationDelay
    wire_trajectory = FreeCAD.ActiveDocument.addObject('Part::Feature','wire_tr')
    wire_tr_folder.addObject(wire_trajectory)
    # n iterator (for wire color)
    n = 0
    # visualization color
    vcolor = FreeCAD.ActiveDocument.WirePath.TrajectoryColor
    # determine the first value for the wire color
    if vcolor == 'Speed':
        mxspeed = FreeCAD.ActiveDocument.WirePath.MaxCutSpeed
        cpspeed = complete_raw_path[2][n][1]
        wire_color = WireColor(cpspeed, mxspeed, 'Speed')

    if vcolor == 'Temperature':
        mxtemp = FreeCAD.ActiveDocument.WirePath.MaxWireTemp
        cptemp = complete_raw_path[2][n][1]
        wire_color = WireColor(cptemp, mxtemp, 'Temperature')

    # animation loop
    for i in range(len(machine_path[0])):
        pa = machine_path[0][i]
        pb = machine_path[1][i]
        # draw wire
        w = Part.makeLine(pa, pb)
        wire.Shape = w
        wire.ViewObject.LineColor = wire_color
        if i < complete_raw_path[2][n][0]:
            # draw wire trajectory
            wire_t_list.append(w)
            wire_trajectory.Shape = Part.makeCompound(wire_t_list)
            wire_trajectory.ViewObject.LineColor = wire_color

        else:
            n += 1
            # create new wire trajectory object
            wire_trajectory = FreeCAD.ActiveDocument.addObject('Part::Feature', 'wire_tr')
            wire_tr_folder.addObject(wire_trajectory)
            # reset compound list
            wire_t_list = []
            wire_t_list.append(w)
            wire_trajectory.Shape = Part.makeCompound(wire_t_list)
            # establish wire color
            if vcolor == 'Speed':
                mxspeed = FreeCAD.ActiveDocument.WirePath.MaxCutSpeed
                cpspeed = complete_raw_path[2][n][1]
                wire_color = WireColor(cpspeed, mxspeed, 'Speed')

            if vcolor == 'Temperature':
                mxtemp = FreeCAD.ActiveDocument.WirePath.MaxWireTemp
                cptemp = complete_raw_path[2][n][1]
                wire_color = WireColor(cptemp, mxtemp, 'Temperature')

            # assign wire color
            wire_trajectory.ViewObject.LineColor = wire_color

        # move machine ---------------------------------------------------
        # side A
        # -XA
        base_XA = XA.Placement.Base
        rot_XA = XA.Placement.Rotation
        base_XA = FreeCAD.Vector(pa.x-xoff, base_XA.y, base_XA.z)
        XA.Placement = FreeCAD.Placement(base_XA, rot_XA)
        # -YA
        base_YA = YA.Placement.Base
        rot_YA = YA.Placement.Rotation
        base_YA = FreeCAD.Vector(pa.x-xoff, pa.y-yoff, base_XA.z)
        YA.Placement = FreeCAD.Placement(base_YA, rot_XA)
        # -XB
        base_XB = XB.Placement.Base
        rot_XB = XB.Placement.Rotation
        base_XB = FreeCAD.Vector(pb.x-xoff, base_XB.y, base_XB.z)
        XB.Placement = FreeCAD.Placement(base_XB, rot_XB)
        # -YB
        base_YB = YB.Placement.Base
        rot_YB = YB.Placement.Rotation
        base_YB = FreeCAD.Vector(pb.x-xoff, pb.y-yoff, base_XB.z)
        YB.Placement = FreeCAD.Placement(base_YB, rot_XB)
        # gui update -------------------------------------------------------
        FreeCAD.Gui.updateGui()
        time.sleep(animation_delay)


def projectEdgeToTrajectory(PA, PB, Z0, Z1):
    # aux function of runSimulation
    # projects shape points to machine workplanes
    pa = FreeCAD.Vector(PA[0], PA[1], PA[2])
    pb = FreeCAD.Vector(PB[0], PB[1], PB[2])
    line_vector = FreeCAD.Vector(PA[0]-PB[0], PA[1]-PB[1], PA[2]-PB[2]).normalize()
    projected_pa = pa + line_vector*(pa[2] - Z0)
    projected_pb = pb - line_vector*(Z1 - pb[2])
    return projected_pa, projected_pb


def WireColor(value, crange, ctype):
    if ctype == 'Temperature':
        k = value / crange*1.0
        r = k
        g = 0.0
        b = 1.0 - k

    if ctype == 'Speed':
        k = value / crange*1.0
        r = 0.0
        g = k
        b = 1.0 - k

    return (r, g, b)
