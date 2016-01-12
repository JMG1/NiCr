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
import Part
import time
from PySide import QtGui


class WirePathFolder:
    def __init__(self, obj):
        obj.addProperty('App::PropertyVector', 'ZeroPoint')
        obj.addProperty('App::PropertyBool', 'UpdateContent')
        obj.addProperty('App::PropertyFloat', 'setCutSpeed')
        obj.addProperty('App::PropertyInteger', 'setWireTemp')
        obj.Proxy = self

    def execute(self, fp):
        pass


class ShapePath:
    def __init__(self, obj, selObj):
        obj.addProperty('App::PropertyString',
                        'ShapeName',
                        'Path Data').ShapeName = selObj.Name

        obj.addProperty('App::PropertyPythonObject',
                        'RawPath',
                        'Path Data')

        obj.addProperty('App::PropertyFloat',
                        'CutSpeed',
                        'Path Settings').CutSpeed = 0.0

        obj.addProperty('App::PropertyFloat',
                        'WireTemperature',
                        'Path Settings').WireTemperature = 0.0

        obj.addProperty('App::PropertyFloat',
                        'PointDensity',
                        'Path Settings',
                        'Path density in mm/point').PointDensity = 6.0

        obj.addProperty('App::PropertyBool',
                        'Reverse',
                        'Path Settings',
                        'Reverses the cut direction of this path').Reverse = False

        obj.addProperty('App::PropertyBool',
                        'ShowMachinePath',
                        'Visualization',
                        'Shows the path projected to the machine sides')

        obj.Proxy = self
        shape = FreeCAD.ActiveDocument.getObject(obj.ShapeName)
        obj.RawPath = ShapeToNiCrPath(shape, obj.PointDensity, reverse=obj.Reverse)
        obj.Shape = PathToShape(obj.RawPath)
        # hide original shape
        FreeCAD.ActiveDocument.getObject(obj.ShapeName).ViewObject.Visibility = False

    def execute(self, fp):
        shape = FreeCAD.ActiveDocument.getObject(fp.ShapeName)
        fp.RawPath = ShapeToNiCrPath(shape, fp.PointDensity, reverse=fp.Reverse)
        fp.Shape = PathToShape(fp.RawPath)
        # TODO send signal to any child object for update


class ShapePathViewProvider:
    def __init__(self,obj):
        obj.Proxy = self

    def getIcon(self):
        import os
        __dir__ = os.path.dirname(__file__)
        return __dir__ + '/icons/WirePath.svg'


class LinkPath:
    def __init__(self, obj, selA, selB):
        obj.addProperty('App::PropertyString',
                        'PathNameA',
                        'Link Data').PathNameA = selA.Object.Name

        obj.addProperty('App::PropertyString',
                        'PathNameB',
                        'Link Data').PathNameB = selB.Object.Name

        obj.addProperty('App::PropertyInteger',
                        'PathIndexA',
                        'Link Data').PathIndexA = pointFromPath(selA.SubObjects[0].Point,
                                                                selA.Object.RawPath)

        obj.addProperty('App::PropertyInteger',
                        'PathIndexB',
                        'Link Data').PathIndexB = pointFromPath(selB.SubObjects[0].Point,
                                                                selB.Object.RawPath)

        obj.addProperty('App::PropertyFloat',
                        'CutSpeed',
                        'Path Settings').CutSpeed = 0.0

        obj.addProperty('App::PropertyFloat',
                        'WireTemperature',
                        'Path Settings').WireTemperature = 0.0

        # add 5 control points
        for i in range(5):
            obj.addProperty('App::PropertyVector',
                            'ControlPoint' + str(i),
                            'Path Control Points')

        obj.addProperty('App::PropertyBool',
                        'update').update = False

        obj.Proxy = self
        # create for the first time
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        # append initial point from pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(obj.PathNameA).RawPath[0][obj.PathIndexA])
        lp_B.append(FreeCAD.ActiveDocument.getObject(obj.PathNameA).RawPath[1][obj.PathIndexA])
        # append destination point in pathshape B
        lp_A.append(FreeCAD.ActiveDocument.getObject(obj.PathNameB).RawPath[0][obj.PathIndexB])
        lp_B.append(FreeCAD.ActiveDocument.getObject(obj.PathNameB).RawPath[1][obj.PathIndexB])
        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        obj.Shape = PathToShape(lp)


    def onChanged(self, fp, prop):
        pass

    def execute(self, fp):
        NiCrMachine_z = FreeCAD.ActiveDocument.NiCrMachine.ZLength
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_B (machine side B = ZLength)
        # append initial point from pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(fp.PathNameA).RawPath[0][fp.PathIndexA])
        lp_B.append(FreeCAD.ActiveDocument.getObject(fp.PathNameA).RawPath[1][fp.PathIndexA])
        # append aux control points
        for i in range(5):
            aux_p = fp.getPropertyByName('ControlPoint' + str(i))
            if ( aux_p.x > 0 or aux_p.y > 0 ) and aux_p.z == 0:
                # draw aux point if it has been modified
                lp_A.append([aux_p.x, aux_p.y, 0.0])
                lp_B.append([aux_p.x, aux_p.y, NiCrMachine_z])

        # append destination point in pathshape B
        lp_A.append(FreeCAD.ActiveDocument.getObject(fp.PathNameB).RawPath[0][fp.PathIndexB])
        lp_B.append(FreeCAD.ActiveDocument.getObject(fp.PathNameB).RawPath[1][fp.PathIndexB])
        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        fp.Shape = PathToShape(lp)
        fp.update = False



class LinkPathViewProvider:
    def __init__(self,obj):
        obj.Proxy = self

    def getIcon(self):
        import os
        __dir__ = os.path.dirname(__file__)
        return __dir__ + '/icons/PathLink.svg'


class InitialPath:
    def __init__(self, obj, selObj):
        obj.addProperty('App::PropertyString',
                        'PathName',
                        'Link Data').PathName = selObj.Object.Name

        obj.addProperty('App::PropertyInteger',
                        'PathIndex',
                        'Link Data').PathIndex = pointFromPath(selObj.SubObjects[0].Point,
                                                               selObj.Object.RawPath)

        obj.addProperty('App::PropertyFloat',
                        'CutSpeed',
                        'Path Settings').CutSpeed = 0.0

        obj.addProperty('App::PropertyFloat',
                        'WireTemperature',
                        'Path Settings').WireTemperature = 0.0

        # add 5 control points
        for i in range(5):
            obj.addProperty('App::PropertyVector',
                            'ControlPoint' + str(i),
                            'Path Control Points')

        obj.addProperty('App::PropertyBool',
                        'update').update = False

        obj.Proxy = self
        # create for the first time
        NiCrMachine = FreeCAD.ActiveDocument.NiCrMachine
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        # append initial point from pathshape A
        lp_A.append(NiCrMachine.VirtualMachineZero)
        lp_B.append(NiCrMachine.VirtualMachineZero + FreeCAD.Vector(0, 0, NiCrMachine.ZLength))
        # append destination point in pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[0][obj.PathIndex])
        lp_B.append(FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[1][obj.PathIndex])
        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        obj.Shape = PathToShape(lp)

    def onChanged(self, fp, prop):
        pass

    def execute(self, fp):
        NiCrMachine = FreeCAD.ActiveDocument.NiCrMachine
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        # append initial point from pathshape A
        lp_A.append(NiCrMachine.VirtualMachineZero)
        lp_B.append(NiCrMachine.VirtualMachineZero + FreeCAD.Vector(0, 0, NiCrMachine.ZLength))
        # append aux control points
        for i in range(5):
            aux_p = fp.getPropertyByName('ControlPoint' + str(i))
            if ( aux_p.x > 0 or aux_p.y > 0 ) and aux_p.z == 0:
                # draw aux point if it has been modified
                lp_A.append([aux_p.x, aux_p.y, 0.0])
                lp_B.append([aux_p.x, aux_p.y, NiCrMachine.ZLength])

        # append destination point in pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[0][fp.PathIndex])
        lp_B.append(FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[1][fp.PathIndex])
        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        fp.Shape = PathToShape(lp)


class InitialPathViewProvider:
    def __init__(self,obj):
        obj.Proxy = self


class FinalPath:
    def __init__(self, obj, selObj):
        obj.addProperty('App::PropertyString',
                        'PathName',
                        'Link Data').PathName = selObj.Object.Name

        obj.addProperty('App::PropertyInteger',
                        'PathIndex',
                        'Link Data').PathIndex = pointFromPath(selObj.SubObjects[0].Point,
                                                               selObj.Object.RawPath)

        obj.addProperty('App::PropertyFloat',
                        'CutSpeed',
                        'Path Settings').CutSpeed = 0.0

        obj.addProperty('App::PropertyFloat',
                        'WireTemperature',
                        'Path Settings').WireTemperature = 0.0

        # add 5 control points
        for i in range(5):
            obj.addProperty('App::PropertyVector',
                            'ControlPoint' + str(i),
                            'Path Control Points')

        obj.addProperty('App::PropertyBool',
                        'PowerOffMachine',
                        'Path Settings').PowerOffMachine = True

        obj.addProperty('App::PropertyBool',
                        'EnableReturnPath',
                        'Path Settings').EnableReturnPath = True

        obj.addProperty('App::PropertyBool',
                        'update').update = False

        obj.Proxy = self
        # create for the first time
        NiCrMachine = FreeCAD.ActiveDocument.NiCrMachine
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        # append initial point from pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[0][obj.PathIndex])
        lp_B.append(FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[1][obj.PathIndex])
        # append destination point in pathshape A
        lp_A.append(NiCrMachine.VirtualMachineZero)
        lp_B.append(NiCrMachine.VirtualMachineZero + FreeCAD.Vector(0, 0, NiCrMachine.ZLength))
        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        obj.Shape = PathToShape(lp)

    def onChanged(self, fp, prop):
        pass

    def execute(self, fp):
        NiCrMachine = FreeCAD.ActiveDocument.NiCrMachine
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        # append initial point from pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[0][fp.PathIndex])
        lp_B.append(FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[1][fp.PathIndex])
        # append aux control points
        for i in range(5):
            aux_p = fp.getPropertyByName('ControlPoint' + str(i))
            if ( aux_p.x > 0 or aux_p.y > 0 ) and aux_p.z == 0:
                # draw aux point if it has been modified
                lp_A.append([aux_p.x, aux_p.y, 0.0])
                lp_B.append([aux_p.x, aux_p.y, NiCrMachine.ZLength])

        # append destination point in pathshape A
        lp_A.append(NiCrMachine.VirtualMachineZero)
        lp_B.append(NiCrMachine.VirtualMachineZero + FreeCAD.Vector(0, 0, NiCrMachine.ZLength))
        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        fp.Shape = PathToShape(lp)


class FinalPathViewProvider:
    def __init__(self, obj):
        obj.Proxy = self


# NiCrPath Functions ----------------------------------------------------------
def CreateCompleteRawPath():
    # recursive link explorer function
    def exploreLink(lobj):
        # explore links and add partial RawPath to the build list
        # auxiliar points
        for i in range(5):
            aux_p = lobj.getPropertyByName('ControlPoint' + str(i))
            if (aux_p.x > 0 or aux_p.y > 0) and aux_p.z == 0:
                # draw aux point if it has been modified
                pr_A.append((aux_p.x, aux_p.y, 0))
                pr_B.append((aux_p.x, aux_p.y, FreeCAD.ActiveDocument.NiCrMachine.ZLength))

        # destination point -> taken from the shapepath
        destPath = FreeCAD.ActiveDocument.getObject(lobj.PathNameB)
        # append partial shapepath
        trigger = False
        for i in range(len(destPath.RawPath[0])+1):
            if not(trigger):
                n = i + lobj.PathIndexB

            if n == len(destPath.RawPath[0]) or trigger:
                n = i + lobj.PathIndexB - len(destPath.RawPath[0])
                trigger = True

            # look for link that derivates from this path
            if i > 0:
                for obj in FreeCAD.ActiveDocument.Objects:
                    try:
                        if obj.PathIndexA == n and obj.PathNameA == destPath.Name:
                            pr_A.append(destPath.RawPath[0][n])
                            pr_B.append(destPath.RawPath[1][n])
                            exploreLink(obj)
                    except:
                        pass

            pr_A.append(destPath.RawPath[0][n])
            pr_B.append(destPath.RawPath[1][n])

    pr_A = []  # partial route A
    pr_B = []  # partial route B
    # initial path and shapepath ----------------------------------------------
    iphobj = FreeCAD.ActiveDocument.InitialPath
    for i in range(5):
        aux_p = iphobj.getPropertyByName('ControlPoint' + str(i))
        if (aux_p.x > 0 or aux_p.y > 0) and aux_p.z == 0:
            # draw aux point if it has been modified
            pr_A.append((aux_p.x, aux_p.y, 0))
            pr_B.append((aux_p.x, aux_p.y, FreeCAD.ActiveDocument.NiCrMachine.ZLength))

    firstSP = FreeCAD.ActiveDocument.getObject(iphobj.PathName)
    trigger = False
    for i in range(len(firstSP.RawPath[0])+1):
        if not(trigger):
            n = i + iphobj.PathIndex

        if n == len(firstSP.RawPath[0]) or trigger:
            n = i + iphobj.PathIndex - len(firstSP.RawPath[0])
            trigger = True

        # look for any link that derivates from this path
        if i > 0:
            for obj in FreeCAD.ActiveDocument.Objects:
                try:
                    if obj.PathIndexA == n and obj.PathNameA == firstSP.Name:
                        pr_A.append(firstSP.RawPath[0][n])
                        pr_B.append(firstSP.RawPath[1][n])
                        exploreLink(obj)
                except:
                    pass

        pr_A.append(firstSP.RawPath[0][n])
        pr_B.append(firstSP.RawPath[1][n])

    # clean geometry
    cl_A = []
    cl_B = []
    pr_A.append(pr_A[0])
    pr_B.append(pr_B[0])
    for i in range(len(pr_A)-1):
        Av0 = pr_A[i]
        Av1 = pr_A[i+1]
        append = True
        if Av0[0] == Av1[0] and Av0[1] == Av1[1] and Av0[2] == Av1[2]:
            append = False

        if append:
            cl_A.append(pr_A[i])
            cl_B.append(pr_B[i])

    complete_raw_path = (cl_A, cl_B)
    return complete_raw_path

#runSimulation(CreateCompleteRawPath())

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
    wirepath = ( Tr_list_A, Tr_list_B )
    # check that sideA  has the lower z value:
    if Tr_list_A[0][2] > Tr_list_B[0][2]:
        wirepath = ( Tr_list_B, Tr_list_A )

    return wirepath


def PathToShape(point_list):
    # creates a compound of faces from a NiCr point list to representate wire
    # trajectory
    comp = []
    for i in range(len(point_list[0])-1):
        pa_0 = FreeCAD.Vector(tuple(point_list[0][i]))
        pa_1 = FreeCAD.Vector(tuple(point_list[0][i+1]))
        pb_0 = FreeCAD.Vector(tuple(point_list[1][i]))
        pb_1 = FreeCAD.Vector(tuple(point_list[1][i+1]))
        l0 = Part.Line(pa_0, pa_1).toShape()
        l1 = Part.Line(pb_0, pb_1).toShape()
        f = Part.makeLoft([l0, l1])
        comp.append(f)

    return Part.makeCompound(comp)




# routing between WirePaths (wirepath path link)

def pointFromPath(vector, raw_path):
    # returns the position of vector in raw_path list
    for side in raw_path:
        for i in range(len(side)):
            v = side[i]
            Fv = FreeCAD.Vector(v[0], v[1], v[2])
            if (Fv-vector).Length < 0.001:
                return i


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
    # write trajectories with compensation for virtual machine ZeroPoint <----
    zeroPoint = FreeCAD.ActiveDocument.NiCrMachine.VirtualMachineZero
    for i in range(len(wirepath[0])):
        AX = str(round(wirepath[0][i][0] - zeroPoint.x, 3)) + ' '
        AY = str(round(wirepath[0][i][1] - zeroPoint.y, 3)) + ' '
        BX = str(round(wirepath[1][i][0] - zeroPoint.x, 3)) + ' '
        BY = str(round(wirepath[1][i][1] - zeroPoint.y, 3)) + '\n'
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
    xoff = FreeCAD.ActiveDocument.NiCrMachine.FrameDiameter*1.5*0
    yoff = FreeCAD.ActiveDocument.NiCrMachine.FrameDiameter*1.8*0
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
        # gui update
        FreeCAD.Gui.updateGui()
        #time.sleep(0.01)
