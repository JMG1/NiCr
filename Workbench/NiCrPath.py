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
        obj.addProperty('App::PropertyVector', 'ZeroPoint', 'Machine Limits')
        obj.addProperty('App::PropertyBool', 'UpdateContent')
        obj.addProperty('App::PropertyFloat', 'MaxCutSpeed', 'Machine Limits')
        obj.addProperty('App::PropertyFloat', 'MaxWireTemp', 'Machine Limits')
        obj.addProperty('App::PropertyFloat', 'setCutSpeed', 'PathSettings')
        obj.addProperty('App::PropertyFloat', 'setWireTemp', 'PathSettings')
        obj.addProperty('App::PropertyEnumeration', 'TrajectoryColor', 'View')
        obj.TrajectoryColor = ['Speed', 'Temperature']
        obj.Proxy = self

    def execute(self, fp):
        for obj in FreeCAD.ActiveDocument.Objects:
            try:
                if obj.CutSpeed == 0:
                    obj.CutSpeed = fp.setCutSpeed

                if obj.WireTemperature == 0:
                    obj.WireTemperature = fp.setWireTemp

            except:
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
        # remove child and parent link objects (they need to be re-defined)
        for obj in FreeCAD.ActiveDocument.Objects:
            try:
                if obj.PathNameA == fp.Name:
                    FreeCAD.ActiveDocument.removeObject(obj.Name)

                if obj.PathNameB == fp.Name:
                    FreeCAD.ActiveDocument.removeObject(obj.Name)

            except AttributeError:
                pass


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
    # recursive link-explorer function
    def exploreLink(lobj):
        # explore links and add partial RawPath to the build list
        # temperature and speed commands
        route_commands.append([len(pr_A)-1, lobj.CutSpeed, lobj.WireTemperature])
        # auxiliar points
        for i in range(5):
            aux_p = lobj.getPropertyByName('ControlPoint' + str(i))
            if (aux_p.x > 0 or aux_p.y > 0) and aux_p.z == 0:
                # draw aux point if it has been modified
                pr_A.append((aux_p.x, aux_p.y, 0))
                pr_B.append((aux_p.x, aux_p.y, FreeCAD.ActiveDocument.NiCrMachine.ZLength))

        # destination point -> taken from the shapepath
        destPath = FreeCAD.ActiveDocument.getObject(lobj.PathNameB)
        # destination path temperature and speed commands
        route_commands.append([len(pr_A)-1, destPath.CutSpeed, destPath.WireTemperature])
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

    # init of the routing script--------------------------------------------
    pr_A = []  # partial route A
    pr_B = []  # partial route B
    route_commands = [] # stores commands issued along the route(speed, temp..)
    # initial path and shapepath ----------------------------------------------
    iphobj = FreeCAD.ActiveDocument.InitialPath
    route_commands.append([len(pr_A)-1, iphobj.CutSpeed, iphobj.WireTemperature])
    for i in range(5):
        aux_p = iphobj.getPropertyByName('ControlPoint' + str(i))
        if (aux_p.x > 0 or aux_p.y > 0) and aux_p.z == 0:
            # draw aux point if it has been modified
            pr_A.append((aux_p.x, aux_p.y, 0))
            pr_B.append((aux_p.x, aux_p.y, FreeCAD.ActiveDocument.NiCrMachine.ZLength))


    firstSP = FreeCAD.ActiveDocument.getObject(iphobj.PathName)
    route_commands.append([len(pr_A)-1, firstSP.CutSpeed, firstSP.WireTemperature])
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

    # initial path speed and temperature commands
    route_commands.append([len(pr_A)-1, iphobj.CutSpeed, iphobj.WireTemperature])
    # append initial path reversed
    for i in range(4, -1, -1):
        aux_p = iphobj.getPropertyByName('ControlPoint' + str(i))
        if (aux_p.x > 0 or aux_p.y > 0) and aux_p.z == 0:
            # draw aux point if it has been modified
            pr_A.append((aux_p.x, aux_p.y, 0))
            pr_B.append((aux_p.x, aux_p.y, FreeCAD.ActiveDocument.NiCrMachine.ZLength))

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
            # re-arrange commands (the have to be displaced as we are removing
            # points from the route)
            for cmd in route_commands:
                if cmd[0] > i:
                    cmd[0] -= 1

        if append:
            cl_A.append(pr_A[i])
            cl_B.append(pr_B[i])

    complete_raw_path = (cl_A, cl_B, route_commands)
    return complete_raw_path


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

    for i in xrange( len( transversal_faces ) ):
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
    for i in xrange(len(consecutive_faces)-1):
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
    for i in xrange( len( clt[0] ) ):
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
    # creates a compound of faces from a NiCr point list to representate the wire
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


def writeNiCrFile(wirepath, directory):
    """
    This functions creates a file containing the .nicr instructions that can be
    read directly by the machine (GCode-like).
    More info about the .nicr language can be found here: > link <
    wirepath[0],wirepath[1] > trajectory points
    wirepath[2] -> wire speed and temperature
    directory = '/home/user/whatever...''
    """
    nicr_file = open(directory + '.nicr', 'w')
    # retrieve basic info
    path_name = FreeCAD.ActiveDocument.WirePath.Label
    mxspeed = FreeCAD.ActiveDocument.WirePath.MaxCutSpeed
    mxtemp = FreeCAD.ActiveDocument.WirePath.MaxWireTemp
    mzero = FreeCAD.ActiveDocument.NiCrMachine.VirtualMachineZero
    zlength = FreeCAD.ActiveDocument.NiCrMachine.ZLength
    # write header
    nicr_file.write('PATH NAME:' + path_name + '\n')
    nicr_file.write('DATE: ' + time.strftime("%c") + '\n')
    nicr_file.write('Exporter version 0.2\n')
    nicr_file.write('SETTINGS ------------------------- \n')
    nicr_file.write('Z AXIS LENGTH: ' + str(zlength) + '\n')
    nicr_file.write('MAX FEED SPEED: ' + str(mxspeed) + '\n')
    nicr_file.write('MAX WIRE TEMPERATURE: ' + str(mxtemp) + '\n')
    nicr_file.write('END SETTINGS --------------------- \n')
    # write machine start
    nicr_file.write('INIT\n')
    nicr_file.write('POWER ON\n')
    # write trajectories with compensation for virtual machine ZeroPoint <----
    zeroPoint = FreeCAD.ActiveDocument.NiCrMachine.VirtualMachineZero
    n = 0
    for i in range(len(wirepath[0])):
        if i == wirepath[2][n][0]:
            nicr_file.write('WIRE ' + str(wirepath[2][n][1]))
            nicr_file.write('SPEED ' + str(wirepath[2][n][2]))
            n += 1

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
    #  TODO -> establish standard header and footer as cura does


def saveNiCrFile():
    FCW = FreeCADGui.getMainWindow()
    save_directory = QtGui.QFileDialog.getSaveFileName(FCW,
                                                       'Save Wirepath as:',
                                                       '/home',
                                                       '.nicr')
    full_path = CreateCompleteRawPath()
    writeNiCrFile(full_path, str(save_directory[0]))
    FreeCAD.Console.PrintMessage('NiCr code saved: ' + str(save_directory[0]) + '\n')


def importNiCrFile():
    FCW = FreeCADGui.getMainWindow()
    file_dir = QtGui.QFileDialog.getOpenFileName(FCW,
                                                 'Load .nicr file:',
                                                 '/home')
    readNiCrFile(file_dir[0])
    FreeCAD.Console.PrintMessage('Path succesfully imported\n')


def readNiCrFile(file_dir):
    nicr_file = open(file_dir, 'r')
    path_A = []
    path_B = []
    zlength = 0
    for line in nicr_file:
        line = line.split(' ')
        if line[0] == 'Z':
            zlength = float(line[3])

        if zlength != 0 and line[0] == 'MOVE':
            path_A.append((float(line[1]), float(line[2]), 0))
            path_B.append((float(line[3]), float(line[4]), zlength))

    complete_path = (path_A, path_B)
    obj = FreeCAD.ActiveDocument.addObject('Part::Feature', 'Imported')
    obj.Shape = PathToShape(complete_path)
