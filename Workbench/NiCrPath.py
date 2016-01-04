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
# NiCrPathV3

import FreeCAD
import FreeCADGui
import Part
import time
from PySide import QtGui

class WirePathFolder:
    def __init__(self, obj):
        obj.addProperty('App::PropertyPythonObject',
                        'ShapeSequence').ShapeSequence = []

        obj.addProperty('App::PropertyFloat',
                        'FeedSpeed',
                        'Path Settings',
                        'Feed speed in mm/second').FeedSpeed = 5.0

        obj.addProperty('App::PropertyInteger',
                        'WireTemperature',
                        'Path Settings',
                        'Wire temperature from 0-255 (0-max)').WireTemperature = 200

        obj.addProperty('App::PropertyVector',
                        'ZeroPoint')

        obj.Proxy = self

    def execute(self, fp):
        pass


def ShapeToNiCrPath(selected_object, precision, reverse=False):
    # Creates the wire path for an input shape. Returns a list of points with
    # a structure: trajectory_list[machine_side][xyz]
    # precision -> distance between discrete points of the trajectory (mm/point)
    #------------------------------------------------------------------------- 0
    # split faces in reference to XY plane
    transversal_faces = []
    parallel_faces = []
    for face in selected_object.Shape.Faces:
        if (face.normalAt(0, 0).cross(FreeCAD.Vector(0, 0, 1))).Length > 0.001:
            transversal_faces.append(face)

        else:
            parallel_faces.append(face)


    def doFacesTouch(face_A, face_B):
        # auxiliar function to test if two faces share and edge
        for edge_A in face_A.Edges:
            for edge_B in face_B.Edges:
                v_AB = (edge_A.CenterOfMass - edge_B.CenterOfMass).Length
                if v_AB < 0.001:
                    return True

        return False

    #------------------------------------------------------------------------- 1
    # order transversal faces to be consecutive
    consecutive_faces = []
    consecutive_faces.append(transversal_faces[0])
    #reverse = True  # reverse the tool trajectory with this boolean
    if reverse:
        transversal_faces.reverse()

    for i in range( len( transversal_faces ) ):
        face_A = consecutive_faces[i]
        for face_B in transversal_faces:
            v_AB = (face_A.CenterOfMass - face_B.CenterOfMass).Length
            if v_AB > 0.001:
                if doFacesTouch( face_A, face_B ):
                    appended = False
                    for face_C in consecutive_faces:
                        if (face_B.CenterOfMass - face_C.CenterOfMass).Length < 0.001:
                            appended = True

                    if not(appended):
                        consecutive_faces.append( face_B )
                        break


    #------------------------------------------------------------------------- 2
    # project path vertexes to a XY plane placed at wire start and end so they form
    # the toolpath
    def vertexesInCommon( face_a, face_b ):
        # aux function to find the vertexes shared by two connected rectangles
        for vertex_a in face_a.Vertexes:
            for vertex_b in face_b.Vertexes:
                if (vertex_a.Point - vertex_b.Point).Length < 0.01:
                    cm_a = vertex_a
                    for v_a in face_a.Vertexes:
                        for v_b in face_b.Vertexes:
                            if (v_a.Point-cm_a.Point).Length > 0.001:
                                if (v_a.Point - v_b.Point ).Length < 0.001:
                                    cm_b = v_a
                                    return cm_a, cm_b


    # discretize length
    #discrete_length = 20 # mm/point
    discrete_length = precision
    consecutive_faces.append(consecutive_faces[0])
    trajectory = []
    for i in range(len(consecutive_faces)-1):
        face_a = consecutive_faces[i]
        face_b = consecutive_faces[i+1]
        cm_a, cm_b = vertexesInCommon( face_a, face_b )
        CG0 = parallel_faces[0].CenterOfMass
        CG1 = parallel_faces[1].CenterOfMass
        edge_list = []
        for edge in face_a.Edges:
            if abs(edge.CenterOfMass.z-CG0.z) < 0.01:
                edge_list.append( edge )

            if abs(edge.CenterOfMass.z-CG1.z)< 0.01:
                edge_list.append( edge )

        tr_edge = []
        for edge in edge_list:
            p1,p2 = edge.discretize(2)
            if (p2-cm_a.Point).Length < 0.01:
                data = [ edge, False ] # 0 or 1 means normal or reverse edge
                tr_edge.append( data )

            elif (p1-cm_a.Point).Length < 0.01:
                data = [ edge, True ]
                tr_edge.append( data )

            if (p2-cm_b.Point).Length < 0.01:
                data = [ edge, False ] # 0 or 1 means normal or reverse edge
                tr_edge.append( data )

            elif (p1-cm_b.Point).Length < 0.01:
                data = [ edge, True ]
                tr_edge.append( data )


        edge_trajectory = []
        if str(edge_list[0].Curve)[1:5] == 'Line' and str(edge_list[1].Curve)[1:5] == 'Line':
            TA = tr_edge[0][0].discretize(2)
            if tr_edge[0][1]:
                TA.reverse()

            TB = tr_edge[1][0].discretize(2)
            if tr_edge[1][1]:
                TB.reverse()

        else:
            n_discretize = max( tr_edge[0][0].Length/discrete_length, tr_edge[1][0].Length/discrete_length )
            n_discretize = max( 2, n_discretize)
            TA = tr_edge[0][0].discretize( int(n_discretize) )
            if tr_edge[0][1]:
                TA.reverse()

            TB = tr_edge[1][0].discretize( int(n_discretize) )
            if tr_edge[1][1]:
                TB.reverse()

        traj_data = [ TA, TB ]
        trajectory.append(traj_data)

    # ------------------------------------------------------------------------ 3
    # trajectory structure
    # trajectory [ faces ] [ sideA, sideB ], [TrajectoryPoints (min of 2) ], [X,Y,Z]
    # -> clean trajectory list from repeated elements:
    clean_list_A = []
    clean_list_B = []
    for pt in trajectory:
        for i in range( len( pt[0] ) -1):
            PA_0 = pt[0][i]
            PA_1 = pt[0][i+1]
            if (PA_0 - PA_1).Length > 0.001:
                clean_list_A.append( pt[0][i] )
                clean_list_B.append( pt[1][i] )
            else:
                pass
    clt = ( clean_list_A, clean_list_B ) # clt -> clean trajectory

    # -> transform trajectory to a simple list to allow JSON serialization (save list)
    Tr_list_A = []
    Tr_list_B = []
    for i in range( len( clt[0] ) ):
        PA = ( clt[0][i].x, clt[0][i].y, clt[0][i].z )
        PB = ( clt[1][i].x, clt[1][i].y, clt[1][i].z )
        Tr_list_A.append( PA )
        Tr_list_B.append( PB )

    Tr_list_A.append( Tr_list_A[0] )
    Tr_list_B.append( Tr_list_B[0] )
    return ( Tr_list_A, Tr_list_B )


def PathToShape( point_list ):
    # creates a compound of face from a NiCr point list to representate wire
    # trajectory
    """ V0
    path_compound = []
    for i in range( len( point_list[0] ) -1):
        if i == len( point_list[0] ) -1:
            PA_0 = tuple(point_list[0][i])
            PA_1 = tuple(point_list[0][0])
            PB_0 = tuple(point_list[1][i])
            PB_1 = tuple(point_list[1][0])

        else:
            PA_0 = tuple(point_list[0][i])
            PA_1 = tuple(point_list[0][i+1])
            PB_0 = tuple(point_list[1][i])
            PB_1 = tuple(point_list[1][i+1])

        w = Part.Wire( [ Part.makeLine( PA_0, PA_1 ),
                         Part.makeLine( PA_1, PB_1 ),
                         Part.makeLine( PB_1, PB_0 ),
                         Part.makeLine( PB_0, PA_0 ) ] )

        path_compound.append( w )

    return Part.makeCompound( path_compound )
    """
    # V1 -> creates surfaces instead of a wire
    # point_list.append(point_list[0])
    comp = []
    for i in range(len(point_list[0])-1):
        pa_0 = FreeCAD.Vector(point_list[0][i])
        pa_1 = FreeCAD.Vector(point_list[0][i+1])
        pb_0 = FreeCAD.Vector(point_list[1][i])
        pb_1 = FreeCAD.Vector(point_list[1][i+1])
        l0 = Part.Line(pa_0, pa_1).toShape()
        l1 = Part.Line(pb_0, pb_1).toShape()
        f = Part.makeLoft([l0, l1])
        comp.append(f)

    return Part.makeCompound(comp)

# wirepath python object class
class WirePath:
    def __init__(self, obj, selObj):
        obj.addProperty('App::PropertyString',
                        'Object_Name',
                        'Path Properties').Object_Name = selObj.Name

        obj.addProperty('App::PropertyFloat',
                        'Wire_Speed',
                        'Path Properties').Wire_Speed = 10.0

        obj.addProperty('App::PropertyFloat',
                        'Wire_Temperature',
                        'Path Properties').Wire_Temperature = 100.0

        obj.addProperty('App::PropertyFloat',
                        'Precision',
                        'Path Properties').Precision = 5.0

        obj.addProperty('App::PropertyBool',
                        'Reverse',
                        'Path Properties').Reverse = False

        obj.addProperty('App::PropertyBool',
                        'Update_Path',
                        'Path Properties').Update_Path = False

        obj.addProperty('App::PropertyBool',
                        'Show_Machine_Path',
                        'PathProperties').Show_Machine_Path = False

        obj.addProperty('App::PropertyPythonObject',
                        'RawPath')

        obj.Proxy = self
        # execute
        obj.RawPath = ShapeToNiCrPath(selObj, obj.Precision)
        obj.Shape = PathToShape(obj.RawPath)
        selObj.ViewObject.Visibility = False

    def execute(self, fp):
        obj = FreeCAD.ActiveDocument.getObject(fp.Object_Name)
        fp.RawPath = ShapeToNiCrPath(obj, fp.Precision, reverse=fp.Reverse)
        fp.Shape = PathToShape(fp.RawPath)


class WirePathViewProvider:
    def __init__(self, obj):
        obj.Proxy = self

    def getIcon(self):
        import os
        __dir__ = os.path.dirname(__file__)
        return __dir__ + '/icons/WirePathIcon.svg'


# routing between WirePaths (wirepath path link)

def pointFromPath(vector, raw_path):
    # returns the position of vector in raw_path list
    for side in raw_path:
        for i in range(len(side)):
            v = side[i]
            Fv = FreeCAD.Vector(v[0], v[1], v[2])
            if (Fv-vector).Length < 0.001:
                return i


class LinkPath:
    def __init__(self, obj):
        # retrieve user selection
        ObjA = FreeCAD.Gui.Selection.getSelectionEx()[0].Object
        PA = FreeCAD.Gui.Selection.getSelectionEx()[0].SubObjects[0]
        ObjB = FreeCAD.Gui.Selection.getSelectionEx()[1].Object
        PB = FreeCAD.Gui.Selection.getSelectionEx()[1].SubObjects[0]
        # link object properties
        obj.addProperty('App::PropertyString',
                        'WirePathA',
                        'Link Properties').WirePathA = ObjA.Name

        obj.addProperty('App::PropertyString',
                        'WirePathB',
                        'Link Properties').WirePathB = ObjB.Name

        obj.addProperty('App::PropertyInteger',
                        'LinkPointA',
                        'Link Properties').LinkPointA = pointFromPath(PA.Point, ObjA.RawPath)

        obj.addProperty('App::PropertyInteger',
                        'LinkPointB',
                        'Link Properties').LinkPointB = pointFromPath(PB.Point, ObjB.RawPath)

        obj.Proxy = self
        PathObjA = FreeCAD.ActiveDocument.getObject(obj.WirePathA)
        PathObjB = FreeCAD.ActiveDocument.getObject(obj.WirePathB)
        PA_0 = PathObjA.RawPath[0][obj.LinkPointA]
        PB_0 = PathObjA.RawPath[1][obj.LinkPointA]
        PA_1 = PathObjB.RawPath[0][obj.LinkPointB]
        PB_1 = PathObjB.RawPath[1][obj.LinkPointB]
        obj.Shape = self.createLinkShape(PA_0, PA_1, PB_0, PB_1)

    def execute(self, fp):
        PathObjA = FreeCAD.ActiveDocument.getObject(fp.WirePathA)
        PathObjB = FreeCAD.ActiveDocument.getObject(fp.WirePathB)
        PA_0 = PathObjA.RawPath[0][fp.LinkPointA]
        PA_1 = PathObjA.RawPath[1][fp.LinkPointA]
        PB_0 = PathObjB.RawPath[0][fp.LinkPointB]
        PB_1 = PathObjB.RawPath[1][fp.LinkPointB]
        fp.Shape = self.createLinkShape(PA_0, PA_1, PB_0, PB_1)

    def createLinkShape(self, PA_0, PA_1, PB_0, PB_1):
        PA_0 = (PA_0[0], PA_0[1], PA_0[2])
        PA_1 = (PA_1[0], PA_1[1], PA_1[2])
        PB_0 = (PB_0[0], PB_0[1], PB_0[2])
        PB_1 = (PB_1[0], PB_1[1], PB_1[2])
        LA = Part.makeLine(PA_0, PA_1)
        LB = Part.makeLine(PB_0, PB_1)
        return Part.makeLoft([LA, LB])


# Create machine path
def createFullPath():
    """
    This function organizes the sequence (cleans) and concatenates the points
    of the linked wirepath objects so they form a unique trajectory of points
    that forms the complete cutpath (excluding initial and final (return home)
    trajectories)
    """
    ShapeSequence = FreeCAD.ActiveDocument.Wirepath.ShapeSequence
    link_objects = []
    for link_name in ShapeSequence:
        link_objects.append(FreeCAD.ActiveDocument.getObject(link_name))

    wirepath_names = []
    # path shapes structure
    for link in link_objects:
        path_names = []
        A = (link.WirePathA, link.LinkPointA)
        path_names.append(A)
        B = (link.WirePathB, link.LinkPointB)
        path_names.append(B)
        for path_name in path_names:
            apnd = True
            for n in wirepath_names:
                if(n[0] == path_name[0]):
                    apnd = False
                    break

            if apnd:
                wirepath_names.append(path_name)

    # raw path concatenation
    ct_A = []  # stands for complete_trajectory_A
    ct_B = []  # stands for complete_trajectory_B
    for wirepath in wirepath_names:
        raw_path = FreeCAD.ActiveDocument.getObject(wirepath[0]).RawPath
        for n in range(len(raw_path[0])-wirepath[1]):
            ct_A.append(raw_path[0][wirepath[1]+n])
            ct_B.append(raw_path[1][wirepath[1]+n])

        for n in range(wirepath[1]):
            ct_A.append(raw_path[0][n])
            ct_B.append(raw_path[1][n])

    complete_trajectory = (ct_A, ct_B)
    return complete_trajectory


def writeNiCrFile(wirepath, wirepath_data, directory):
    """
    This functions creates a file containing the .nicr instructions that can be
    read directly by the machine (GCode-like).
    wirepath = ((A0,A1...An),(B0,B1...Bn)) -> An, Bn == 3D point (x,y,z)
    wirepath_data = ( name, settings, feed_speed, temperature...)
    directory = '/home/user/whatever...''
    """
    nicr_file = open(directory + '.nicr', 'w')
    # write header
    nicr_file.write('PATH NAME:' + wirepath_data[1] + '\n')
    nicr_file.write('DATE: ' + time.strftime("%c") + '\n')
    nicr_file.write('SETTINGS ------------------------- \n')
    nicr_file.write('FEED SPEED: ' + str(wirepath_data[2]) + '\n')
    nicr_file.write('WIRE TEMP: ' + str(wirepath_data[3]) + '\n')
    nicr_file.write('END SETTINGS --------------------- \n')
    # write machine start
    nicr_file.write('INIT\n')
    nicr_file.write('POWER ON\n')
    nicr_file.write('WIRE ' + str(wirepath_data[3]) + '\n')
    # write trajectories
    for i in range(len(wirepath[0])):
        AX = str(round(wirepath[0][i][0], 3)) + ' '
        AY = str(round(wirepath[0][i][1], 3)) + ' '
        BX = str(round(wirepath[1][i][0], 3)) + ' '
        BY = str(round(wirepath[1][i][1], 3)) + '\n'
        ins = 'MOVE ' + AX + AY + BX + BY
        nicr_file.write(ins)
    # write machine shutdown
    nicr_file.write('POWER OFF\n')
    nicr_file.write('END')
    # close file
    nicr_file.close()
    FreeCAD.Console.PrintMessage('NiCr code generated succesfully\n')


def saveNiCrFile():
    FCW = FreeCADGui.getMainWindow()
    cpfolder = FreeCAD.ActiveDocument.Wirepath
    save_directory = QtGui.QFileDialog.getSaveFileName(FCW,
                                                       'Save Wirepath as:',
                                                       '/home',
                                                       '.nicr')
    full_path = createFullPath()
    wirepath_data = ('test', '', cpfolder.FeedSpeed, cpfolder.WireTemperature)
    writeNiCrFile(full_path, wirepath_data, str(save_directory[0]))
    FreeCAD.Console.PrintMessage('NiCr code saved: ' + str(save_directory[0]) + '\n')


def projectEdgeToTrajectory(PA, PB, Z0, Z1):
    # aux function of runSimulation
    # projects shape points to machine workplanes
    pa = FreeCAD.Vector(PA[0], PA[1], PA[2])
    pb = FreeCAD.Vector(PB[0], PB[1], PB[2])
    line_vector = FreeCAD.Vector(PA[0]-PB[0], PA[1]-PB[1], PA[2]-PB[2]).normalize()
    projected_pa = pa + line_vector*(pa[2] - Z0)
    projected_pb = pb - line_vector*(Z1 - pb[2])
    return projected_pa, projected_pb


def runSimulation(complete_raw_path):
    # FreeCAD.ActiveDocument.WirePath.ViewObject.Visibility = False
    projected_trajectory_A = []
    projected_trajectory_B = []
    Z0 = FreeCAD.ActiveDocument.NiCrMachine.FrameDiameter*1.1
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
        FreeCAD.ActiveDocument.SimMachine.addObject(wire)

    try:
        wire_trajectory = FreeCAD.ActiveDocument.WireTrajectory
    except:
        wire_trajectory = FreeCAD.ActiveDocument.addObject('Part::Feature','WireTrajectory')
        FreeCAD.ActiveDocument.SimMachine.addObject(wire_trajectory)
        wire_trajectory.ViewObject.LineColor = (1.0, 0.0, 0.0)
        wire_trajectory.ViewObject.LineWidth = 1.0

    # retrieve machine shapes
    XA = FreeCAD.ActiveDocument.XA
    XB = FreeCAD.ActiveDocument.XB
    YA = FreeCAD.ActiveDocument.YA
    YB = FreeCAD.ActiveDocument.YB
    # ofsets
    xoff = FreeCAD.ActiveDocument.NiCrMachine.FrameDiameter*1.5
    yoff = FreeCAD.ActiveDocument.NiCrMachine.FrameDiameter*1.8
    # animation loop
    wire_t_list = []
    for i in range(len(machine_path[0])):
        pa = machine_path[0][i]
        pb = machine_path[1][i]
        # draw wire
        w = Part.makeLine(pa, pb)
        wire.Shape = w
        # draw wire trajectory
        wire_t_list.append(w)
        wire_trajectory.Shape = Part.makeCompound(wire_t_list)
        # side A
        # -XA
        base_XA = XA.Placement.Base
        rot_XA = XA.Placement.Rotation
        base_XA = FreeCAD.Vector(pa.x-xoff, base_XA.y, base_XA.z)
        XA.Placement = FreeCAD.Placement(base_XA, rot_XA)
        # -YA
        base_YA = YA.Placement.Base
        rot_YA = YA.Placement.Rotation
        base_YA = FreeCAD.Vector(pa.x-xoff, pb.y-yoff, base_XA.z)
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
        # gui update
        FreeCAD.Gui.updateGui()
        time.sleep(0.01)
