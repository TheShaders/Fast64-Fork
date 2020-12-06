import ctypes
import os
import numpy as np

dir = os.path.dirname(os.path.abspath(__file__))
bvh_lib = ctypes.CDLL(os.path.join(dir, "bvh_py"))

bvh_lib.createBvh.restype = ctypes.c_void_p
bvh_lib.numNodes.restype = ctypes.c_uint64
bvh_lib.getNodeBounds.restype = ctypes.POINTER(ctypes.c_float)
bvh_lib.getNodeTriIndices.restype = ctypes.POINTER(ctypes.c_uint64)
bvh_lib.getNodeFirstChildIndex.restype = ctypes.c_uint64

class BvhNode:
    def __init__(self, min, max, children, tris):
        self.min = min
        self.max = max
        self.children = children
        self.isLeaf = (len(children) == 0)
        self.tris = tris


class Bvh:
    def __init__(self, name):
        self.c_bvh = ctypes.c_void_p(bvh_lib.createBvh())
        self.name = name
        self.unorderedTris = []
        self.unorderedTypes = []
        self.orderedTris = []
        self.orderedTypes = []
        self.nodeFirstTris = {} # Keys and values are original indices
        self.nodesReordered = []
        self.nodesMissNext = {0: -1} # Keys and values are original indices
        self.nodeParents = {0: -1} # Keys and values are original indices
        self.nodeIsLeft = {-1: True, 0 : False} # Keys are original indices
    def __del__(self):
        bvh_lib.freeBvh(self.c_bvh)
    def AddTris(self, tris, surfaceType):
        c_tris = (ctypes.c_float * 3 * 3 * len(tris))()
        for triIndex, tri in enumerate(tris):
            for vertIndex, vert in enumerate(tri[0]):
                c_tris[triIndex][vertIndex][0] = ctypes.c_float(vert[0])
                c_tris[triIndex][vertIndex][1] = ctypes.c_float(vert[1])
                c_tris[triIndex][vertIndex][2] = ctypes.c_float(vert[2])
        bvh_lib.addTris(self.c_bvh, c_tris, len(tris))
        self.unorderedTris.extend(tris)
        self.unorderedTypes.extend([surfaceType] * len(tris))
    def Compute(self):
        bvh_lib.computeBvh(self.c_bvh)

        curNodeIndex = 0
        # Reorder the bvh so that are ordered in hit traversal order
        while curNodeIndex != -1:
            print("New node: " + str(curNodeIndex))
            self.nodesReordered.append(curNodeIndex)
            nodeTriCount = self.GetNodeTriCount(curNodeIndex)

            # if self.nodeIsLeft[curNodeIndex] == True:

            # Record the parent of this node's children (which would be this node) if this node is not a leaf
            # This will be used to walk back up the tree to find the next node in hit traversal order
            if nodeTriCount == 0:
                childIndexL = self.GetNodeFirstChildIndex(curNodeIndex)
                childIndexR = childIndexL + 1
                self.nodeParents[childIndexL] = curNodeIndex
                self.nodeParents[childIndexR] = curNodeIndex
                self.nodeIsLeft[childIndexL] = True
                self.nodeIsLeft[childIndexR] = False
                print("Moving to left child of node: " + str(curNodeIndex))
                curNodeIndex = childIndexL
            else:
                # Move up until we find a parent node that is a left node, and then move to it's right sibling
                while not self.nodeIsLeft[curNodeIndex]:
                    print("Moving up from node: " + str(curNodeIndex))
                    curNodeIndex = self.nodeParents[curNodeIndex]
                if curNodeIndex == -1:
                    break
                print("Moving to right sibling of node: " + str(curNodeIndex))
                curNodeIndex += 1
        
        for curNodeIndex in self.nodesReordered:
            missNodeIndex = curNodeIndex
            # Move up until we find a parent node that is a left node, and then move to it's right sibling
            while not self.nodeIsLeft[missNodeIndex]:
                missNodeIndex = self.nodeParents[missNodeIndex]
            if missNodeIndex != -1:
                missNodeIndex += 1
            self.nodesMissNext[curNodeIndex] = self.nodesReordered.index(missNodeIndex) if missNodeIndex != -1 else -1

        for i in self.nodesReordered:
            self.nodeFirstTris[i] = len(self.orderedTris)
            for triIndex in self.GetNodeTriIndices(i):
                self.orderedTris.append(self.unorderedTris[triIndex])
                self.orderedTypes.append(self.unorderedTypes[triIndex])
    def GetNodeCount(self):
        return int(bvh_lib.numNodes(self.c_bvh))
    def GetNodeBounds(self, index):
        c_bounds = bvh_lib.getNodeBounds(self.c_bvh, ctypes.c_uint64(index))
        return ((np.float32(c_bounds[0]), np.float32(c_bounds[2]), np.float32(c_bounds[4])), (np.float32(c_bounds[1]), np.float32(c_bounds[3]), np.float32(c_bounds[5])))
    def IsLeafNode(self, index):
        return bool(bvh_lib.getNodeIsLeaf(self.c_bvh, ctypes.c_uint64(index)))
    def GetNodeTriCount(self, index):
        return int(bvh_lib.getNodeTriCount(self.c_bvh, ctypes.c_uint64(index)))
    def GetNodeTriIndices(self, index):
        triCount = self.GetNodeTriCount(index)
        c_indices = bvh_lib.getNodeTriIndices(self.c_bvh, ctypes.c_uint64(index))
        indices = []
        for i in range(triCount):
            indices.append(int(c_indices[i]))
        return indices
    def GetNodeFirstChildIndex(self, index):
        return int(bvh_lib.getNodeFirstChildIndex(self.c_bvh, ctypes.c_uint64(index)))
    def to_c(self):
        if self.c_bvh is None:
            return ''

        typeArrayDef = 'SurfaceType ' + self.name + '_surface_types[] = {'
        triArrayDef = 'ColTri ' + self.name + '_tris[] = {'
        for triIndex, triData in enumerate(self.orderedTris):
            tri = triData[0]
            u = tri[1] - tri[0]
            v = tri[2] - tri[0]
            normal = u.cross(v)
            normal.normalize()
            uu = u.dot(u)
            uv = u.dot(v)
            vv = v.dot(v)
            originDist = -tri[0].dot(normal)
            if triIndex % 2 == 0:
                triArrayDef += '\n    '
            triArrayDef += '{' + '{' + ', '.join(map(str, normal)) + '}, ' + str(originDist) + ', '
            triArrayDef += '{' + ', '.join(map(str, tri[0])) + '}, ' 
            triArrayDef += '{' + ', '.join(map(str, u)) + '}, '
            triArrayDef += '{' + ', '.join(map(str, v)) + '}, '
            triArrayDef += str(uu) + ', ' + str(uv) + ', ' + str(vv) + '}, '
            if triIndex % 16 == 0:
                typeArrayDef += '\n    '
            typeArrayDef += str(self.orderedTypes[triIndex]) + ', '
        triArrayDef += '\n};\n'
        typeArrayDef += '\n};\n'

        bvhArrayDef = 'BVHNode ' + self.name + '_nodes[] = {'
        for newNodeIndex, nodeIndex in enumerate(self.nodesReordered):
            nodeTriCount = self.GetNodeTriCount(nodeIndex)
            nodeBounds = self.GetNodeBounds(nodeIndex)

            nodeFirstTri = self.nodeFirstTris[nodeIndex] if nodeTriCount != 0 else 0

            nodeMissLink = self.nodesMissNext[nodeIndex]

            if nodeIndex % 1 == 0:
                bvhArrayDef += '\n    '
            bvhArrayDef += '{' + str(nodeTriCount) + ', ' + str(nodeFirstTri) + ', ' + str(nodeMissLink) + ', 0, '
            bvhArrayDef += '{' + '{' + ', '.join(map(str, nodeBounds[0])) + '}, {' + ', '.join(map(str, nodeBounds[1])) + '}' + '}' + '}, '
        bvhArrayDef += '\n};\n'

        bvhTreeDef  = 'BVHTree ' + self.name + '_tree = {\n'
        bvhTreeDef += '    ' + str(len(self.orderedTris)) + ',\n'
        bvhTreeDef += '    ' + str(self.GetNodeCount()) + ',\n'
        bvhTreeDef += '    ' + self.name + '_tris,\n'
        bvhTreeDef += '    ' + self.name + '_nodes,\n'
        bvhTreeDef += '    ' + self.name + '_surface_types,\n'
        bvhTreeDef += '};\n'

        return typeArrayDef + '\n' + triArrayDef + '\n' + bvhArrayDef + '\n' + bvhTreeDef


bvh_lib.enableDebug()
