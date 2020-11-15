import bpy
import mathutils
import math
import copy

from os.path import basename
import os
from io import BytesIO

from .sm64_geolayout_bone import getSwitchOptionBone
from .sm64_geolayout_constants import *
from .sm64_geolayout_utility import *
from .utility import *
from .sm64_constants import *
from .f3d_writer import *
from .sm64_camera import saveCameraSettingsToGeolayout
from .sm64_geolayout_classes import *

def appendSecondaryGeolayout(geoDirPath, geoName1, geoName2, additionalNode = ''):
	geoPath = os.path.join(geoDirPath, 'geo.inc.c')
	geoFile = open(geoPath, 'a', newline='\n')
	geoFile.write('\n\nconst GeoLayout ' + geoName2 + '_geo[] = {\n' +\
		(('\t' + additionalNode + ',\n') if additionalNode is not None else '') +\
		'\tGEO_BRANCH(1, ' + geoName1 + '_geo),\n' +\
		'\tGEO_END(),\n};\n')
	geoFile.close()

def replaceDLReferenceInGeo(geoPath, pattern, replacement):
	if not os.path.exists(geoPath):
		return
	geoFile = open(geoPath, 'r', newline = '\n')
	geoData = geoFile.read()
	geoFile.close()

	newData = re.sub(pattern, replacement, geoData, flags = re.DOTALL)
	if newData != geoData:
		geoFile = open(geoPath, 'w', newline = '\n')
		geoFile.write(newData)
		geoFile.close()

def prepareGeolayoutExport(armatureObj, obj):
	# Make object and armature space the same.
	setOrigin(armatureObj, obj)

	# Apply armature scale.
	bpy.ops.object.select_all(action = "DESELECT")
	armatureObj.select_set(True)
	bpy.context.view_layer.objects.active = armatureObj
	bpy.ops.object.transform_apply(location = False, rotation = False,
		scale = True, properties = False)

def getAllArmatures(armatureObj, currentArmatures):
	linkedArmatures = []
	for bone in armatureObj.data.bones:
		if bone.geo_cmd == 'Switch':
			for switchOption in bone.switch_options:
				if switchOption.switchType == 'Mesh':
					if switchOption.optionArmature is None:
						raise PluginError('"' + bone.name + '" in armature "' +\
							armatureObj.name + '" has a mesh switch option ' +\
							'with no defined mesh.')
					elif switchOption.optionArmature not in linkedArmatures and \
						switchOption.optionArmature not in currentArmatures:
						linkedArmatures.append(switchOption.optionArmature)
	
	currentArmatures.extend(linkedArmatures)
	for linkedArmature in linkedArmatures:
		getAllArmatures(linkedArmature, currentArmatures)

def getCameraObj(camera):
	for obj in bpy.data.objects:
		if obj.data == camera:
			return obj
	raise PluginError('The level camera ' + camera.name + \
		' is no longer in the scene.')

def appendRevertToGeolayout(geolayoutGraph, fModel):
	fModel.materialRevert = GfxList(fModel.name + "_" + 'material_revert_render_settings', fModel.DLFormat)
	revertMatAndEndDraw(fModel.materialRevert, 
		[DPSetEnvColor(0xFF, 0xFF, 0xFF, 0xFF),
		DPSetAlphaCompare("G_AC_NONE")])

	drawLayers = geolayoutGraph.getDrawLayers()

	# Revert settings in each draw layer
	for i in drawLayers:
		dlNode = DisplayListNode(i)
		dlNode.DLmicrocode = fModel.materialRevert

		# Assume first node is start render area
		# This is important, since a render area groups things separately.
		# If we added these nodes outside the render area, they would not happen
		# right after the nodes inside.
		geolayoutGraph.startGeolayout.nodes[0].children.append(TransformNode(dlNode))

# Convert to Geolayout
def convertArmatureToGeolayout(armatureObj, obj, convertTransformMatrix, 
	f3dType, isHWv1, camera, name, modelName, DLFormat, convertTextureData):
	
	fModel = Model(f3dType, modelName)

	if len(armatureObj.children) == 0:
		raise PluginError("No mesh parented to armature.")

	obj.data.calc_loop_triangles()
	obj.data.calc_normals_split()
	infoDict = getInfoDict(obj)

	# Find start bone, which is not root. Root is the start for animation.
	startBoneNames = findStartBones(armatureObj)
	
	convertTransformMatrix = convertTransformMatrix @ \
		mathutils.Matrix.Diagonal(armatureObj.scale).to_4x4()

	# Start geolayout
	#if camera is not None:
	#	geolayoutGraph = GeolayoutGraph(name)
	#	cameraObj = getCameraObj(camera)
	#	meshGeolayout = saveCameraSettingsToGeolayout(
	#		geolayoutGraph, cameraObj, armatureObj, name + "_geo")
	#else:
	#	geolayoutGraph = GeolayoutGraph(name + "_geo")
	#	rootNode = TransformNode(StartNode())
	#	geolayoutGraph.startGeolayout.nodes.append(rootNode)
	#	meshGeolayout = geolayoutGraph.startGeolayout
	
	for i in range(len(startBoneNames)):
		startBoneName = startBoneNames[i]
		if i > 0:
			meshGeolayout.nodes.append(TransformNode(StartNode()))
		processBone(fModel, startBoneName, obj, armatureObj, 
			convertTransformMatrix, None, None, None, 
			[], name, None, infoDict, convertTextureData)
	#generateSwitchOptions(meshGeolayout.nodes[0], meshGeolayout, geolayoutGraph,
	#	name)
	#appendRevertToGeolayout(geolayoutGraph, fModel)
	#geolayoutGraph.generateSortedList()
	#if DLFormat == 'SM64 Function Node':
	#	geolayoutGraph.convertToDynamic()
	return fModel

# Camera is unused here
def convertObjectToGeolayout(obj, convertTransformMatrix, 
	f3dType, isHWv1, camera, name, modelName, fModel, areaObj, DLFormat, convertTextureData):
	
	if fModel is None:
		fModel = Model(f3dType, modelName)
		#fModel = FModel(f3dType, isHWv1, name, DLFormat)
	
	#convertTransformMatrix = convertTransformMatrix @ \
	#	mathutils.Matrix.Diagonal(obj.scale).to_4x4()

	# Start geolayout
	if areaObj is not None:
		#geolayoutGraph = GeolayoutGraph(name)
		#cameraObj = getCameraObj(camera)
		#meshGeolayout = saveCameraSettingsToGeolayout(
		#	geolayoutGraph, areaObj, obj, name + '_geo')
		rootObj = areaObj
		fModel.global_data.fog_color = areaObj.area_fog_color
		fModel.global_data.fog_position = areaObj.area_fog_position
	else:
		#geolayoutGraph = GeolayoutGraph(name + '_geo')
		#rootNode = TransformNode(StartNode())
		#geolayoutGraph.startGeolayout.nodes.append(rootNode)
		#meshGeolayout = geolayoutGraph.startGeolayout
		rootObj = obj

	# Duplicate objects to apply scale / modifiers / linked data
	tempObj, allObjs = \
		duplicateHierarchy(rootObj, 'ignore_render', True, None if areaObj is None else areaObj.areaIndex)
	try:
		processMesh(fModel, tempObj, convertTransformMatrix, None, convertTextureData)
		cleanupDuplicatedObjects(allObjs)
		rootObj.select_set(True)
		bpy.context.view_layer.objects.active = rootObj
	except Exception as e:
		cleanupDuplicatedObjects(allObjs)
		rootObj.select_set(True)
		bpy.context.view_layer.objects.active = rootObj
		raise Exception(str(e))

	# appendRevertToGeolayout(geolayoutGraph, fModel)
	#geolayoutGraph.generateSortedList()
	#if DLFormat == "SM64 Function Node":
	#	geolayoutGraph.convertToDynamic()
	return fModel

# C Export
def exportGeolayoutArmatureC(armatureObj, obj, convertTransformMatrix, 
	f3dType, isHWv1, dirPath, texDir, savePNG, texSeparate, camera, groupName, 
	headerType, dirName, geoName, levelName, customExport, DLFormat):
	fModel = convertArmatureToGeolayout(armatureObj, obj,
		convertTransformMatrix, f3dType, isHWv1, camera, dirName, geoName, DLFormat, not savePNG)

	return saveGeolayoutC(geoName, dirName, fModel, dirPath, texDir, 
		savePNG, texSeparate, groupName, headerType, levelName, customExport, DLFormat)

def exportModelFromMesh(obj, convertTransformMatrix, 
	f3dType, isHWv1, dirPath, texDir, savePNG, texSeparate, camera, groupName, 
	headerType, dirName, geoName, levelName, customExport, DLFormat):
	fModel = convertObjectToGeolayout(obj, 
		convertTransformMatrix, f3dType, isHWv1, camera, dirName, geoName, None, None, DLFormat, not savePNG)

	return saveGeolayoutC(geoName, dirName, fModel, dirPath, texDir, 
		savePNG, texSeparate, groupName, headerType, levelName, customExport, DLFormat)

def saveGeolayoutC(geoName, dirName, fModel, exportDir, texDir, savePNG,
 	texSeparate, groupName, headerType, levelName, customExport, DLFormat):
	dirPath, texDir = getExportDir(customExport, exportDir, headerType, 
		levelName, texDir, dirName)

	dirName = toAlnum(dirName)
	groupName = toAlnum(groupName)
	geoDirPath = os.path.join(dirPath, toAlnum(dirName))

	if not os.path.exists(geoDirPath):
		os.mkdir(geoDirPath)
	
	if headerType == 'Actor':
		scrollName = 'actor_geo_' + dirName
	elif headerType == 'Level':
		scrollName = levelName + '_level_geo_' + dirName
	#static_data, dynamic_data, texC, scroll_data = fModel.to_c(texSeparate, savePNG, texDir, scrollName)
	static_data = fModel.to_c()
	dynamic_data = ''
	texC = ''
	scroll_data = ''
	#cDefineStatic, cDefineDynamic, cDefineScroll = fModel.to_c_def(scrollName)
	cDefineStatic = ''
	cDefineDynamic = ''
	cDefineScroll = ''
	#geolayoutGraph.startGeolayout.name = geoName
	#geoData = geolayoutGraph.to_c()

	if headerType == 'Actor':
		matCInclude = '#include "assets/' + dirName + '/material.inc.c"'
		matHInclude = '#include "assets/' + dirName + '/material.inc.h"'
		headerInclude = '#include "assets/' + dirName + '/geo_header.h"'

		if not customExport:
			# Group name checking, before anything is exported to prevent invalid state on error.
			if groupName == '' or groupName is None:
				raise PluginError("Actor header type chosen but group name not provided.")

			# groupPathC = os.path.join(dirPath, groupName + ".c")
			# groupPathGeoC = os.path.join(dirPath, groupName + "_geo.c")
			# groupPathH = os.path.join(dirPath, groupName + ".h")

			# if not os.path.exists(groupPathC):
			# 	raise PluginError(groupPathC + ' not found.\n Most likely issue is that \"' + groupName + '\" is an invalid group name.')
			# elif not os.path.exists(groupPathGeoC):
			# 	raise PluginError(groupPathGeoC + ' not found.\n Most likely issue is that \"' + groupName + '\" is an invalid group name.')
			# elif not os.path.exists(groupPathH):
			# 	raise PluginError(groupPathH + ' not found.\n Most likely issue is that \"' + groupName + '\" is an invalid group name.')

	else:
		matCInclude = '#include "levels/' + levelName + '/' + dirName + '/material.inc.c"'
		matHInclude = '#include "levels/' + levelName + '/' + dirName + '/material.inc.h"'
		headerInclude = '#include "levels/' + levelName + '/' + dirName + '/geo_header.h"'
	
	if not bpy.context.scene.disableScroll:
		writeTexScrollFiles(exportDir, geoDirPath, cDefineScroll, scroll_data)
	
	#if DLFormat == "Static":
	static_data += '\n' + dynamic_data
	cDefineStatic = '' #geolayoutGraph.to_c_def() + cDefineStatic + cDefineDynamic
	#else:
	#	geoData = writeMaterialFiles(exportDir, geoDirPath, 
	#		headerInclude, matHInclude,
	#		cDefineDynamic, dynamic_data, geoData, customExport)

	modelPath = os.path.join(geoDirPath, 'model.inc.c')
	modelFile = open(modelPath, 'w', newline='\n')
	modelFile.write(static_data)
	modelFile.close()

	if texSeparate:
		texPath = os.path.join(geoDirPath, 'texture.inc.c')
		texFile = open(texPath, 'w', newline='\n')
		texFile.write(texC)
		texFile.close()

	#fModel.freePalettes()

	# save geolayout
	#geoPath = os.path.join(geoDirPath, 'geo.inc.c')
	#geoFile = open(geoPath, 'w', newline='\n')
	#geoFile.write(geoData)
	#geoFile.close()

	# save header
	headerPath = os.path.join(geoDirPath, 'geo_header.h')
	cDefFile = open(headerPath, 'w', newline='\n')
	cDefFile.write(cDefineStatic)
	cDefFile.close()
	
	#if not customExport:
	#	if headerType == 'Actor':
	#		# Write to group files
	#		# groupPathC = os.path.join(dirPath, groupName + ".c")
	#		# groupPathGeoC = os.path.join(dirPath, groupName + "_geo.c")
	#		# groupPathH = os.path.join(dirPath, groupName + ".h")
#
	#		# writeIfNotFound(groupPathC, '\n#include "' + dirName + '/model.inc.c"', '')
	#		# writeIfNotFound(groupPathGeoC, '\n#include "' + dirName + '/geo.inc.c"', '')
	#		# writeIfNotFound(groupPathH, '\n#include "' + dirName + '/geo_header.h"', '\n#endif')
#
	#		texscrollIncludeC = '#include "assets/' + dirName + '/texscroll.inc.c"'
	#		texscrollIncludeH = '#include "assets/' + dirName + '/texscroll.inc.h"'
	#		texscrollGroup = groupName
	#		texscrollGroupInclude = '#include "assets/' + groupName + '.h"'
#
	#	elif headerType == 'Level':
	#		# groupPathC = os.path.join(dirPath, "leveldata.c")
	#		# groupPathGeoC = os.path.join(dirPath, "geo.c")
	#		# groupPathH = os.path.join(dirPath, "header.h")
#
	#		# writeIfNotFound(groupPathC, '\n#include "levels/' + levelName + '/' + dirName + '/model.inc.c"', '')
	#		# writeIfNotFound(groupPathGeoC, '\n#include "levels/' + levelName + '/' + dirName + '/geo.inc.c"', '')
	#		# writeIfNotFound(groupPathH, '\n#include "levels/' + levelName + '/' + dirName + '/geo_header.h"', '\n#endif')
#
	#		texscrollIncludeC = '#include "levels/' + levelName + '/' + dirName + '/texscroll.inc.c"'
	#		texscrollIncludeH = '#include "levels/' + levelName + '/' + dirName + '/texscroll.inc.h"'
	#		texscrollGroup = levelName
	#		texscrollGroupInclude = '#include "levels/' + levelName + '/header.h"'
#
	#	if not bpy.context.scene.disableScroll:
	#		writeTexScrollHeadersGroup(exportDir, texscrollIncludeC, texscrollIncludeH, 
	#			texscrollGroup, cDefineScroll, texscrollGroupInclude)
	#	
	#	if DLFormat != "Static": # Change this
	#		writeMaterialHeaders(exportDir, matCInclude, matHInclude)

	#if savePNG:
	#	if not customExport and headerType == 'Level':
	#		fModel.save_textures(dirPath)
	#	else:
	#		fModel.save_textures(geoDirPath)
	
	return cDefineStatic


# Switch Handling Process
# When convert armature to geolayout node hierarchy, mesh switch options
# are converted to switch node children, but material/draw layer options
# are converted to SwitchOverrideNodes. During this process, any material
# override geometry will be generated as well.

# Afterward, the node hierarchy is traversed again, and any SwitchOverride
# nodes are converted to actual geolayout node hierarchies.
def generateSwitchOptions(transformNode, geolayout, geolayoutGraph, prefix):
	if isinstance(transformNode.node, JumpNode):
		for node in transformNode.node.geolayout.nodes:
			generateSwitchOptions(node, transformNode.node.geolayout, 
			geolayoutGraph, prefix)
	overrideNodes = []
	if isinstance(transformNode.node, SwitchNode):
		switchName = transformNode.node.name
		prefix += '_' + switchName
		#prefix = switchName
		i = 0
		while i < len(transformNode.children):
			prefixName = prefix + '_opt' + str(i)
			childNode = transformNode.children[i]
			if isinstance(childNode.node, SwitchOverrideNode):
				drawLayer = childNode.node.drawLayer
				material = childNode.node.material
				specificMat = childNode.node.specificMat
				overrideType = childNode.node.overrideType

				# This should be a 0xB node
				#copyNode = duplicateNode(transformNode.children[0],
				#	transformNode, transformNode.children.index(childNode))
				index = transformNode.children.index(childNode)
				transformNode.children.remove(childNode)

				# Switch option bones should have unique names across all 
				# armatures.
				optionGeolayout = geolayoutGraph.addGeolayout(
					childNode, prefixName)
				geolayoutGraph.addJumpNode(transformNode, geolayout,
					optionGeolayout, index)
				optionGeolayout.nodes.append(TransformNode(StartNode()))
				copyNode = optionGeolayout.nodes[0]

				#i -= 1
				# Assumes first child is a start node, where option 0 is
				# assumes overrideChild starts with a Start node
				option0Nodes = [transformNode.children[0]]
				if len(option0Nodes) == 1 and \
					isinstance(option0Nodes[0].node, StartNode):
					for startChild in option0Nodes[0].children:
						generateOverrideHierarchy(copyNode, startChild, 
							material, specificMat, overrideType, drawLayer,
							option0Nodes[0].children.index(startChild),
							optionGeolayout, geolayoutGraph, 
							optionGeolayout.name)
				else:
					for overrideChild in option0Nodes:
						generateOverrideHierarchy(copyNode, overrideChild, 
							material, specificMat, overrideType, drawLayer,
							option0Nodes.index(overrideChild),
							optionGeolayout, geolayoutGraph, 
							optionGeolayout.name)
				if material is not None:
					overrideNodes.append(copyNode)
			i += 1
	for i in range(len(transformNode.children)):
		childNode = transformNode.children[i]
		if isinstance(transformNode.node, SwitchNode):
			prefixName = prefix + '_opt' + str(i)
		else:
			prefixName = prefix
		
		if childNode not in overrideNodes:
			generateSwitchOptions(childNode, geolayout, geolayoutGraph, prefixName)

def generateOverrideHierarchy(parentCopyNode, transformNode, 
	material, specificMat, overrideType, drawLayer, index, geolayout,
	geolayoutGraph, switchOptionName):
	#print(transformNode.node)
	if isinstance(transformNode.node, SwitchOverrideNode) and \
		material is not None:
		return

	copyNode = TransformNode(copy.copy(transformNode.node))
	copyNode.parent = parentCopyNode
	parentCopyNode.children.insert(index, copyNode)
	if isinstance(transformNode.node, JumpNode):
		jumpName = switchOptionName + '_jump_' +\
			transformNode.node.geolayout.name
		jumpGeolayout = geolayoutGraph.addGeolayout(transformNode, jumpName)
		oldGeolayout = copyNode.node.geolayout
		copyNode.node.geolayout = jumpGeolayout
		geolayoutGraph.addGeolayoutCall(geolayout, jumpGeolayout)
		startNode = TransformNode(StartNode())
		jumpGeolayout.nodes.append(startNode)
		if len(oldGeolayout.nodes) == 1 and \
			isinstance(oldGeolayout.nodes[0].node, StartNode):
			for node in oldGeolayout.nodes[0].children:
				generateOverrideHierarchy(startNode, node, material, specificMat,
				overrideType, drawLayer, 
				oldGeolayout.nodes[0].children.index(node),
				jumpGeolayout, geolayoutGraph, jumpName)
		else:
			for node in oldGeolayout.nodes:
				generateOverrideHierarchy(startNode, node, material, specificMat,
				overrideType, drawLayer, oldGeolayout.nodes.index(node),
				jumpGeolayout, geolayoutGraph, jumpName)

	elif not isinstance(copyNode.node, SwitchOverrideNode) and\
		copyNode.node.hasDL:
		if material is not None:
			copyNode.node.DLmicrocode = \
				copyNode.node.fMesh.drawMatOverrides[(material, specificMat, overrideType)]
		if drawLayer is not None:
			copyNode.node.drawLayer = drawLayer

	for child in transformNode.children:
		generateOverrideHierarchy(copyNode, child, material, specificMat, 
			overrideType, drawLayer, transformNode.children.index(child),
			geolayout, geolayoutGraph, switchOptionName)
		
def addParentNode(parentTransformNode, geoNode):
	transformNode = TransformNode(geoNode)
	transformNode.parent = parentTransformNode
	parentTransformNode.children.append(transformNode)
	return transformNode

def duplicateNode(transformNode, parentNode, index):
	optionNode = TransformNode(copy.copy(transformNode.node))
	optionNode.parent = parentNode
	parentNode.children.insert(index, optionNode)
	return optionNode

def partOfGeolayout(obj):
	useGeoEmpty = obj.data is None and \
		(obj.sm64_obj_type == 'None' or \
		obj.sm64_obj_type == 'Level Root' or \
		obj.sm64_obj_type == 'Area Root' or \
		obj.sm64_obj_type == 'Switch')
	return isinstance(obj.data, bpy.types.Mesh) or useGeoEmpty

def getSwitchChildren(areaRoot):
	geoChildren = [child for child in areaRoot.children if partOfGeolayout(child)]
	alphabeticalChildren = sorted(geoChildren, key = lambda childObj: childObj.original_name)
	return alphabeticalChildren

def setRooms(obj, roomIndex = None):
	# Child objects
	if roomIndex is not None:
		obj.room_num = roomIndex
		for childObj in obj.children:
			setRooms(childObj, roomIndex)

	# Area root object
	else:
		alphabeticalChildren = getSwitchChildren(obj)
		for i in range(len(alphabeticalChildren)):
			setRooms(alphabeticalChildren[i], i + 1) # index starts at 1

def isZeroRotation(rotate):
	eulerRot = rotate.to_euler(geoNodeRotateOrder)
	return convertEulerFloatToShort(eulerRot[0]) == 0 and \
		convertEulerFloatToShort(eulerRot[1]) == 0 and \
		convertEulerFloatToShort(eulerRot[2]) == 0

def isZeroTranslation(translate):
	return convertFloatToShort(translate[0]) == 0 and \
		convertFloatToShort(translate[1]) == 0 and \
		convertFloatToShort(translate[2]) == 0

def getOptimalNode(translate, rotate, drawLayer, hasDL, zeroTranslation, zeroRotation):

	if zeroRotation and zeroTranslation:
		node = DisplayListNode(drawLayer)
	elif zeroRotation:
		node = TranslateNode(drawLayer, hasDL, translate)
	elif zeroTranslation: 
		# This case never happens as rotations are applied when hierarchy is duplicated
		node = RotateNode(drawLayer, hasDL, rotate)
	else:
		node = TranslateRotateNode(drawLayer, 0, hasDL, translate, rotate)
	return node

# This function should be called on a copy of an object
# The copy will have modifiers / scale applied and will be made single user
def processMesh(fModel, obj, transformMatrix, parentBone,
	convertTextureData):
		
	# Its okay to return if ignore_render, because when we duplicated obj hierarchy we stripped all
	# ignore_renders from geolayout.
	if not partOfGeolayout(obj) or obj.ignore_render:
		return

	if parentBone is None:
		translate = mathutils.Vector((0,0,0))
		rotate = mathutils.Quaternion()
	else:
		translate = obj.matrix_local.decompose()[0]
		rotate = obj.matrix_local.decompose()[1]
	rotAxis, rotAngle = rotate.to_axis_angle()
	zeroRotation = isZeroRotation(rotate)
	zeroTranslation = isZeroTranslation(translate)
	
	curBone = Bone(transformMatrix @ translate)

	if obj.data is None:
		meshGroup = None
	else:
		meshGroup = saveStaticModel(fModel, obj, transformMatrix, fModel.name, "Static", convertTextureData, False)
		curBone.addLayer(obj.draw_layer_static, meshGroup)

	fModel.addBone(curBone, parentBone)

	# Todo bone translation

	alphabeticalChildren = sorted(obj.children, key = lambda childObj: childObj.original_name)
	for childObj in alphabeticalChildren:
		processMesh(fModel, childObj, transformMatrix, curBone, convertTextureData)

# need to remember last geometry holding parent bone.
# to do skinning, add the 0x15 command before any non-geometry bone groups.
# 

# transformMatrix is a constant matrix to apply to verts, 
# not related to heirarchy.

# lastTransformParentName: last parent with mesh data.
# lastDeformParentName: last parent in transform node category.
# this may or may not include mesh data.

# If an armature is rotated, its bones' local_matrix will remember original
# rotation. Thus we don't want a bone's matrix relative to armature, but
# relative to the root bone of the armature.

def processBone(fModel, boneName, obj, armatureObj, transformMatrix,
	lastTranslateName, lastRotateName, lastDeformName,
	materialOverrides, namePrefix, parentBone, infoDict, convertTextureData):
	bone = armatureObj.data.bones[boneName]
	poseBone = armatureObj.pose.bones[boneName]
	boneGroup = poseBone.bone_group
	finalTransform = copy.deepcopy(transformMatrix)
	materialOverrides = copy.copy(materialOverrides)
	
	if bone.geo_cmd == 'Ignore':
		return

	# Get translate
	if lastTranslateName is not None:
		translateParent = armatureObj.data.bones[lastTranslateName]
		translate = bone.matrix_local.decompose()[0] - translateParent.matrix_local.decompose()[0]
	else:
		translateParent = None
		translate = bone.matrix_local.decompose()[0]

	# Get rotate
	if lastRotateName is not None:
		rotateParent = armatureObj.data.bones[lastRotateName]
		rotate = (rotateParent.matrix_local.inverted() @ \
			bone.matrix_local).decompose()[1]
	else:
		rotateParent = None
		rotate = bone.matrix_local.decompose()[1]

	lastTranslateName = boneName
	lastRotateName = boneName

	rotation = rotate.to_matrix().to_4x4()

	newBone = Bone(translate * bpy.context.scene.blenderToN64Scale)

	curRotation = bone.matrix_local.inverted().decompose()[1].to_matrix().to_4x4()

	meshGroup, makeLastDeformBone = saveModelGivenVertexGroup(
		fModel, obj, bone.name, lastDeformName,
		finalTransform @ curRotation.inverted(), armatureObj, materialOverrides, 
		namePrefix, infoDict, bone.draw_layer, convertTextureData)
	
	finalTransform = rotation.inverted() @ transformMatrix

		

	if meshGroup is not None:
		if not bone.use_deform:
			raise PluginError(bone.name + " has vertices in its vertex group but is not set to deformable. Make sure to enable deform on this bone.")
		if lastDeformName is not None and \
			armatureObj.data.bones[lastDeformName].geo_cmd == 'SwitchOption' \
			and meshGroup.skinnedMesh is not None:
			raise PluginError("Cannot skin geometry to a Switch Option " +\
				"bone. Skinning cannot occur across a switch node.")
		newBone.addLayer(bone.draw_layer, meshGroup)
		lastDeformName = boneName
		
	fModel.addBone(newBone, parentBone)

	#print(boneGroup.name if boneGroup is not None else "Offset")
	if len(bone.children) > 0: 
		# nextStartNode = TransformNode(StartNode())
		# transformNode.children.append(nextStartNode)
		# nextStartNode.parent = transformNode

		childrenNames = sorted([bone.name for bone in bone.children])
		for name in childrenNames:
			processBone(fModel, name, obj, armatureObj, 
				finalTransform, lastTranslateName, lastRotateName, 
				lastDeformName, materialOverrides, 
				namePrefix, newBone, infoDict, convertTextureData)
			#transformNode.children.append(childNode)
			#childNode.parent = transformNode

	# bone = armatureObj.data.bones[boneName]
	# for switchIndex in range(len( bone.switch_options)):
	# 	switchOption = bone.switch_options[switchIndex]
	# 	if switchOption.switchType == 'Mesh':
	# 		optionArmature = switchOption.optionArmature
	# 		if optionArmature is None:
	# 			raise PluginError('Error: In switch bone ' + boneName +\
	# 				' for option ' + str(switchIndex) + \
	# 				', the switch option armature is None.')
	# 		elif not isinstance(optionArmature.data, bpy.types.Armature):
	# 			raise PluginError('Error: In switch bone ' + boneName +\
	# 				' for option ' + str(switchIndex) + \
	# 				', the object provided is not an armature.')
	# 		elif optionArmature in geolayoutGraph.secondaryGeolayouts:
	# 			optionGeolayout = geolayoutGraph.secondaryGeolayouts[
	# 				optionArmature]
	# 			geolayoutGraph.addJumpNode(
	# 				transformNode, geolayout, optionGeolayout)
	# 			continue

	# 		#optionNode = addParentNode(switchTransformNode, StartNode())
			
	# 		optionBoneName = getSwitchOptionBone(optionArmature)
	# 		optionBone = optionArmature.data.bones[optionBoneName]

	# 		# Armature doesn't matter here since node is not based off bone
	# 		optionGeolayout = \
	# 			geolayoutGraph.addGeolayout(
	# 				optionArmature, namePrefix + "_" + optionArmature.name)
	# 		geolayoutGraph.addJumpNode(transformNode, geolayout, 
	# 			optionGeolayout)
			
	# 		rotAxis, rotAngle = rotate.to_axis_angle()
	# 		if rotAngle > 0.00001 or translate.length > 0.0001:
	# 			startNode = TransformNode(
	# 				TranslateRotateNode(1, 0, False, translate, rotate))
	# 		else:
	# 			startNode = TransformNode(StartNode())
	# 		optionGeolayout.nodes.append(startNode)

	# 		childrenNames = sorted(
	# 			[bone.name for bone in optionBone.children])
	# 		for name in childrenNames:
	# 			# We can use optionBone as the last translate/rotate
	# 			# since we added a TranslateRotate node before
	# 			# the switch node.
	# 			optionObjs = []
	# 			for childObj in optionArmature.children:
	# 				if isinstance(childObj.data, bpy.types.Mesh):
	# 					optionObjs.append(childObj)
	# 			if len(optionObjs) > 1:
	# 				raise PluginError('Error: In switch bone ' + boneName +\
	# 				' for option ' + str(switchIndex) + \
	# 				', the switch option armature has more than one mesh child.')
	# 			elif len(optionObjs) < 1:
	# 				raise PluginError('Error: In switch bone ' + boneName +\
	# 				' for option ' + str(switchIndex) + \
	# 				', the switch option armature has no mesh children.')
	# 			optionObj = optionObjs[0]
	# 			optionObj.data.calc_loop_triangles()
	# 			optionObj.data.calc_normals_split()
	# 			optionInfoDict = getInfoDict(optionObj)
	# 			processBone(fModel, name, optionObj,
	# 				optionArmature,
	# 				finalTransform, optionBone.name, optionBone.name,
	# 				optionBone.name, startNode,
	# 				materialOverrides, namePrefix + '_' + optionBone.name, 
	# 				optionGeolayout, geolayoutGraph, optionInfoDict, convertTextureData)
	# 	else:
	# 		if switchOption.switchType == 'Material':
	# 			material = switchOption.materialOverride
	# 			if switchOption.overrideDrawLayer:
	# 				drawLayer = int(switchOption.drawLayer)
	# 			else:
	# 				drawLayer = None
	# 			if switchOption.materialOverrideType == 'Specific':
	# 				specificMat = tuple([matPtr.material for matPtr in \
	# 					switchOption.specificOverrideArray])
	# 			else:
	# 				specificMat = tuple([matPtr.material for matPtr in \
	# 					switchOption.specificIgnoreArray])
	# 		else:
	# 			material = None
	# 			specificMat = None
	# 			drawLayer = int(switchOption.drawLayer)
			
	# 		overrideNode = TransformNode(SwitchOverrideNode(
	# 			material, specificMat, drawLayer,
	# 			switchOption.materialOverrideType))
	# 		overrideNode.parent = transformNode
	# 		transformNode.children.append(overrideNode)

def processSwitchBoneMatOverrides(materialOverrides, switchBone):
	for switchOption in switchBone.switch_options:
		if switchOption.switchType == 'Material':
			if switchOption.materialOverride is None:
				raise PluginError("Error: On switch bone " + \
					switchBone.name + ', a switch option' + \
					' is a Material Override, but no material is provided.')
			if switchOption.materialOverrideType == 'Specific':
				for mat in switchOption.specificOverrideArray:
					if mat is None:
						raise PluginError("Error: On switch bone " + \
							switchBone.name + ', a switch option' + \
							' has a material override field that is None.')
				specificMat = tuple([matPtr.material for matPtr in \
							switchOption.specificOverrideArray])		
			else:
				for mat in switchOption.specificIgnoreArray:
					if mat is None:
						raise PluginError("Error: On switch bone " + \
							switchBone.name + ', a switch option' + \
							' has a material ignore field that is None.')
				specificMat = tuple([matPtr.material for matPtr in \
							switchOption.specificIgnoreArray])

			materialOverrides.append((switchOption.materialOverride, specificMat,
				switchOption.materialOverrideType))

def getGroupIndexFromname(obj, name):
	for group in obj.vertex_groups:
		if group.name == name:
			return group.index
	return None

def getGroupNameFromIndex(obj, index):
	for group in obj.vertex_groups:
		if group.index == index:
			return group.name
	return None

def getGroupIndex(vert, armatureObj, obj):
	actualGroups = []
	belowLimitGroups = []
	nonBoneGroups = []
	for group in vert.groups:
		groupName = getGroupNameFromIndex(obj, group.group)
		if groupName is not None:
			if groupName in armatureObj.data.bones:
				if group.weight > 0.4:
					actualGroups.append(group)
				else:
					belowLimitGroups.append(groupName)
			else:
				nonBoneGroups.append(groupName)

	if len(actualGroups) == 0:
		highlightWeightErrors(obj, [vert], "VERT")
		raise VertexWeightError("All vertices must be part of a vertex group, be non-trivially weighted (> 0.4), and the vertex group must correspond to a bone in the armature.\n" +\
			"Groups of the bad vert that don't correspond to a bone: " + str(nonBoneGroups) + '. If a vert is supposed to belong to this group then either a bone is missing or you have the wrong group.\n' +\
			"Groups of the bad vert below weight limit: " + str(belowLimitGroups) + \
			". If a vert is supposed to belong to one of these groups then make sure to increase its weight.")
	vertGroup = actualGroups[0]
	significantWeightGroup = None
	for group in actualGroups:
		if group.weight > 0.5:
			if significantWeightGroup is None:
				significantWeightGroup = group
			else:
				highlightWeightErrors(obj, [vert], "VERT")
				raise VertexWeightError("A vertex was found that was significantly weighted to multiple groups. Make sure each vertex only belongs to one group whose weight is greater than 0.5. (" + \
					getGroupNameFromIndex(obj, group.group) + ', ' + getGroupNameFromIndex(obj, significantWeightGroup.group) + ')')
		if group.weight > vertGroup.weight:
			vertGroup = group
	#if vertGroup not in actualGroups:
	#raise VertexWeightError("A vertex was found that was primarily weighted to a group that does not correspond to a bone in #the armature. (" + getGroupNameFromIndex(obj, vertGroup.group) + ') Either decrease the weights of this vertex group or remove it. If you think this group should correspond to a bone, make sure to check your spelling.')
	return vertGroup.group

class SkinnedFace():
	def __init__(self, bFace, loopsInGroup, loopsNotInGroup):
		self.bFace= bFace
		self.loopsInGroup = loopsInGroup
		self.loopsNotInGroup = loopsNotInGroup

def checkIfFirstNonASMNode(childNode):
	index = childNode.parent.children.index(childNode)
	if index == 0:
		return True
	while index > 0 and \
		(isinstance(childNode.parent.children[index - 1].node, FunctionNode) or \
		not childNode.parent.children[index - 1].skinned):
		index -= 1
	return index == 0

# parent connects child node to itself
# skinned node handled by child

# A skinned mesh node should be before a mesh node.
# However, other transform nodes may exist in between two mesh nodes,
# So the skinned mesh node must be inserted before any of those transforms.
# Sibling mesh nodes thus cannot share the same transform nodes before it
# If they are both deform.
# Additionally, ASM nodes should count as modifiers for other nodes if 
# they precede them
def addSkinnedMeshNode(armatureObj, boneName, skinnedMesh, transformNode, parentNode):
	# Add node to its immediate parent
	#print(str(type(parentNode.node)) + str(type(transformNode.node)))
	parentNode.children.append(transformNode)
	transformNode.parent = parentNode

	if skinnedMesh is None:
		return transformNode
	else:
		transformNode.skinned = True
		#print("Skinned mesh exists.")

	# Get skinned node
	bone = armatureObj.data.bones[boneName]
	skinnedNode = DisplayListNode(int(bone.draw_layer))
	skinnedNode.fMesh = skinnedMesh
	skinnedNode.DLmicrocode = skinnedMesh.draw
	skinnedTransformNode = TransformNode(skinnedNode)

	# Ascend heirarchy until reaching first node before a deform parent.
	# We duplicate the hierarchy along the way to possibly use later.
	highestChildNode = transformNode
	transformNodeCopy = TransformNode(copy.copy(transformNode.node))
	transformNodeCopy.parent = parentNode
	highestChildCopy = transformNodeCopy
	isFirstChild = True
	hasNonDeform0x13Command = False
	acrossSwitchNode = False
	while highestChildNode.parent is not None and\
		not (highestChildNode.parent.node.hasDL or highestChildNode.parent.skinnedWithoutDL): # empty 0x13 command?
		isFirstChild &= checkIfFirstNonASMNode(highestChildNode)
		hasNonDeform0x13Command |= isinstance(highestChildNode.parent.node,
			DisplayListWithOffsetNode)

		acrossSwitchNode |= isinstance(highestChildNode.parent.node, SwitchNode)
			
		highestChildNode = highestChildNode.parent
		highestChildCopyParent = TransformNode(copy.copy(highestChildNode.node))
		highestChildCopyParent.children = [highestChildCopy]
		highestChildCopy.parent = highestChildCopyParent
		#print(str(highestChildCopy.node) + " " + str(isFirstChild))
		highestChildCopy = highestChildCopyParent
	#isFirstChild &= checkIfFirstNonASMNode(highestChildNode)
	if highestChildNode.parent is None:
		raise PluginError("Issue with \"" + boneName + "\": Deform parent bone not found for skinning.")
		#raise PluginError("There shouldn't be a skinned mesh section if there is no deform parent. This error may have ocurred if a switch option node is trying to skin to a parent but no deform parent exists.")

	# Otherwise, remove the transformNode from the parent and 
	# duplicate the node heirarchy up to the last deform parent.
	# Add the skinned node first to the last deform parent,
	# then add the duplicated node hierarchy afterward.
	if highestChildNode != transformNode:
		if not isFirstChild:
			#print("Hierarchy but not first child.")
			if hasNonDeform0x13Command:
				raise PluginError("Error with " + boneName + ': You cannot have more that one child skinned mesh connected to a parent skinned mesh with a non deform 0x13 bone in between. Try removing any unnecessary non-deform bones.')
		
			if acrossSwitchNode:
				raise PluginError("Error with " + boneName + ': You can not' +\
				' skin across a switch node with more than one child.')

			# Remove transformNode
			parentNode.children.remove(transformNode)
			transformNode.parent = None

			# copy hierarchy, along with any preceding Function commands
			highestChildIndex = \
				highestChildNode.parent.children.index(highestChildNode)
			precedingFunctionCmds = []
			while highestChildIndex > 0 and \
				type(highestChildNode.parent.children[\
				highestChildIndex - 1].node) is FunctionNode:

				precedingFunctionCmds.insert(0, copy.deepcopy(
					highestChildNode.parent.children[highestChildIndex - 1]))
				highestChildIndex -= 1
			#_____________
			# add skinned mesh node
			highestChildCopy.parent = highestChildNode.parent
			highestChildCopy.parent.children.append(skinnedTransformNode)
			skinnedTransformNode.parent = highestChildCopy.parent

			# add Function cmd nodes
			for asmCmdNode in precedingFunctionCmds:
				highestChildCopy.parent.children.append(asmCmdNode)

			# add heirarchy to parent
			highestChildCopy.parent.children.append(highestChildCopy)

			transformNode = transformNodeCopy
		else:
			#print("Hierarchy with first child.")
			nodeIndex = highestChildNode.parent.children.index(highestChildNode)
			while nodeIndex > 0 and \
				type(highestChildNode.parent.children[\
				nodeIndex - 1].node) is FunctionNode:
				nodeIndex -= 1
			highestChildNode.parent.children.insert(
				nodeIndex, skinnedTransformNode)
			skinnedTransformNode.parent = highestChildNode.parent
	else:
		#print("Immediate child.")
		nodeIndex = parentNode.children.index(transformNode)
		parentNode.children.insert(nodeIndex, skinnedTransformNode)
		skinnedTransformNode.parent = parentNode	

	return transformNode	

def getAncestorGroups(parentGroup, vertexGroup, armatureObj, obj):
    if parentGroup is None:
        return []
    ancestorBones = []
    processingBones = [armatureObj.data.bones[vertexGroup]]
    while len(processingBones) > 0:
        currentBone = processingBones[0]
        processingBones = processingBones[1:]
        
        ancestorBones.append(currentBone)
        processingBones.extend(currentBone.children)
    
    currentBone = armatureObj.data.bones[vertexGroup].parent
    while currentBone is not None and currentBone.name != parentGroup:
        ancestorBones.append(currentBone)
        currentBone = currentBone.parent
    ancestorBones.append(armatureObj.data.bones[parentGroup])
    
    #print(vertexGroup + ", " + parentGroup)
    #print([bone.name for bone in ancestorBones])
    return [getGroupIndexFromname(obj, bone.name) for bone in armatureObj.data.bones if bone not in ancestorBones]


def checkUniqueBoneNames(fModel, name, vertexGroup):
	if name in fModel.meshGroups:
		raise PluginError(vertexGroup + " has already been processed. Make " +\
			"sure this bone name is unique, even across all switch option " +\
			"armatures.")

# returns fMeshGroup, makeLastDeformBone
def saveModelGivenVertexGroup(fModel, obj, vertexGroup, 
	parentGroup, transformMatrix, armatureObj, materialOverrides, namePrefix,
	infoDict, drawLayer, convertTextureData):
	#checkForF3DMaterial(obj)

	mesh = obj.data
	currentGroupIndex = getGroupIndexFromname(obj, vertexGroup)
	vertIndices = [vert.index for vert in obj.data.vertices if\
		getGroupIndex(vert, armatureObj, obj) == currentGroupIndex]
	parentGroupIndex = getGroupIndexFromname(obj, parentGroup) \
		if parentGroup is not None else -1

	ancestorGroups = getAncestorGroups(parentGroup, vertexGroup, armatureObj, obj)

	if len(vertIndices) == 0:
		print("No vert indices in " + vertexGroup)
		return None, False

	bone = armatureObj.data.bones[vertexGroup]
	
	currentMatrix = mathutils.Matrix.Scale(1 * bpy.context.scene.blenderToN64Scale, 4) @ \
		bone.matrix_local.inverted()
		
		
	currentRot = bone.matrix.to_4x4()
	print('  ' + str(bone.matrix.to_quaternion()))
	currentMatrix = transformMatrix @ currentRot @ mathutils.Matrix.Translation(bone.matrix_local.decompose()[0]).inverted()
	
	# if parentGroup is None:
	# 	parentMatrix = mathutils.Matrix.Scale(1 * bpy.context.scene.blenderToN64Scale, 4)
	# else:
	# 	parentBone = armatureObj.data.bones[parentGroup]
	# 	parentMatrix = mathutils.Matrix.Scale(1 * bpy.context.scene.blenderToN64Scale, 4) @ \
	# 	parentBone.matrix_local.inverted()

	parentMatrix = transformMatrix
	
	# dict of material_index keys to face array values
	groupFaces = {}
	
	# dict of material_index keys to SkinnedFace objects
	skinnedFaces = {}

	handledFaces = []
	for vertIndex in vertIndices:
		if vertIndex not in infoDict['vert']:
			continue
		for face in infoDict['vert'][vertIndex]:
			# Ignore repeat faces
			if face in handledFaces:
				continue
			else:
				handledFaces.append(face)

			loopsInGroup = []
			loopsNotInGroup = []
			isChildSkinnedFace = False

			# loop is interpreted as face + loop index
			for i in range(3):
				vertGroupIndex = \
					getGroupIndex(mesh.vertices[face.vertices[i]], 
						armatureObj, obj)
				if vertGroupIndex == currentGroupIndex:
					loopsInGroup.append((face, mesh.loops[face.loops[i]]))
				elif vertGroupIndex == parentGroupIndex:
					loopsNotInGroup.append((face, mesh.loops[face.loops[i]]))
				elif vertGroupIndex not in ancestorGroups:
					# Only want to handle skinned faces connected to parent
					isChildSkinnedFace = True
					break
				else:
					highlightWeightErrors(obj, [face], 'FACE')
					raise VertexWeightError("Error with " + vertexGroup + ": Verts attached to one bone can not be attached to any of its ancestor or sibling bones besides its first immediate deformable parent bone. For example, a foot vertex can be connected to a leg vertex, but a foot vertex cannot be connected to a thigh vertex.")
			if isChildSkinnedFace:
				continue
			
			if len(loopsNotInGroup) == 0:
				if face.material_index not in groupFaces:
					groupFaces[face.material_index] = []
				groupFaces[face.material_index].append(face)
			else:
				if face.material_index not in skinnedFaces:
					skinnedFaces[face.material_index] = []
				skinnedFaces[face.material_index].append(
					SkinnedFace(face, loopsInGroup, loopsNotInGroup))

	# Save skinned mesh
	if len(skinnedFaces) > 0:
		#print("Skinned")
		fMeshGroup = saveSkinnedMeshByMaterial(skinnedFaces, fModel,
			vertexGroup, obj, currentMatrix, parentMatrix, namePrefix, 
			infoDict, vertexGroup, drawLayer, convertTextureData)
	elif len(groupFaces) > 0:
		fMeshGroup = FMeshGroup(toAlnum(namePrefix + \
			('_' if namePrefix != '' else '') + vertexGroup), 
			FMesh(toAlnum(namePrefix + \
			('_' if namePrefix != '' else '') + vertexGroup) + '_mesh', fModel.DLFormat), None, fModel.DLFormat)
	else:
		print("No faces in " + vertexGroup)
		return None, True
	
	# Save mesh group
	checkUniqueBoneNames(fModel, toAlnum(namePrefix + \
		('_' if namePrefix != '' else '') + vertexGroup), vertexGroup)
	fModel.meshGroups[toAlnum(namePrefix + vertexGroup)] = fMeshGroup

	# Save unskinned mesh
	for material_index, bFaces in groupFaces.items():
		material = obj.data.materials[material_index]
		checkForF3dMaterialInFaces(obj, material)
		saveMeshByFaces(material, bFaces, 
			fModel, fMeshGroup.mesh, obj, currentMatrix, infoDict, drawLayer, convertTextureData)
	
	# End mesh drawing
	# Reset settings to prevent issues with other models
	#revertMatAndEndDraw(fMeshGroup.mesh.draw)
	fMeshGroup.mesh.draw.commands.extend([
		SPEndDisplayList(),
	])

	# Must be done after all geometry saved
	for (material, specificMat, overrideType) in materialOverrides:
		if fMeshGroup.mesh is not None:
			saveOverrideDraw(obj, fModel, material, specificMat, overrideType,
			fMeshGroup.mesh, drawLayer, convertTextureData)
		if fMeshGroup.skinnedMesh is not None:
			saveOverrideDraw(obj, fModel, material, specificMat, overrideType,
			fMeshGroup.skinnedMesh, drawLayer, convertTextureData)
	
	return fMeshGroup, True

def saveOverrideDraw(obj, fModel, material, specificMat, overrideType, fMesh, drawLayer, convertTextureData):
	fOverrideMat, texDimensions = \
		saveOrGetF3DMaterial(material, fModel, obj, drawLayer, convertTextureData)
	overrideIndex = str(len(fMesh.drawMatOverrides))
	if (material, specificMat, overrideType) in fMesh.drawMatOverrides:
		overrideIndex = fMesh.drawMatOverrides[(material, specificMat, overrideType)].name[-1]
	meshMatOverride = GfxList(
		fMesh.name + '_mat_override_' + toAlnum(material.name) + \
		'_' + overrideIndex, fModel.DLFormat)
	#print(fMesh.drawMatOverrides)
	#print('fdddddddddddddddd ' + str(fMesh.name) + " " + str(material) + " " + str(specificMat) + " " + str(overrideType))
	fMesh.drawMatOverrides[(material, specificMat, overrideType)] = meshMatOverride
	removeReverts = []
	triCommands = []
	for command in fMesh.draw.commands:
		meshMatOverride.commands.append(copy.copy(command))
	for command in meshMatOverride.commands:
		if isinstance(command, SPDisplayList):
			for (modelMaterial, modelDrawLayer), (fMaterial, texDimensions) in \
				fModel.materials.items():
				shouldModify = \
					(overrideType == 'Specific' and modelMaterial in specificMat) or \
					(overrideType == 'All' and modelMaterial not in specificMat)
				if command.displayList == fMaterial.material and shouldModify:
					#print(fOverrideMat.material.name)
					command.displayList = fOverrideMat.material
					triCommand = meshMatOverride.commands[meshMatOverride.commands.index(command) + 1]
					if triCommand not in triCommands:
						triCommands.append(triCommand)
						
				if command.displayList == fMaterial.revert and shouldModify:
					removeReverts.append(command)
	for command in removeReverts:
		meshMatOverride.commands.remove(command)
	if fOverrideMat.revert is not None:
		for command in triCommands:
			meshMatOverride.commands.insert(meshMatOverride.commands.index(command) + 1, 
			SPDisplayList(fOverrideMat.revert))

	#else:
	#	meshMatOverride.commands.append(SPDisplayList(fOverrideMat.material))
	#	for triList in fMesh.triangleLists:
	#		meshMatOverride.commands.append(SPDisplayList(triList))
	#	if fOverrideMat.revert is not None:
	#		meshMatOverride.commands.append(SPDisplayList(fOverrideMat.revert))
	#	meshMatOverride.commands.append(SPEndDisplayList())		

def findVertIndexInBuffer(loop, buffer, loopDict):
	i = 0
	for material_index, vertData in buffer:
		for f3dVert in vertData:
			if f3dVert == loopDict[loop]:
				return i
			i += 1
	#print("Can't find " + str(loop))
	return -1

def convertVertDictToArray(vertDict):
	data = []
	matRegions = {}
	for material_index, vertData in vertDict:
		start = len(data)
		data.extend(vertData)
		end = len(data)
		matRegions[material_index] = (start, end)
	return data, matRegions

# This collapses similar loops together IF they are in the same material.
def splitSkinnedFacesIntoTwoGroups(skinnedFaces, fModel, obj, uv_data, drawLayer, convertTextureData):
	inGroupVertArray = []
	notInGroupVertArray = []

	# For selecting on error
	notInGroupBlenderVerts = []
	loopDict = {}
	for material_index, skinnedFaceArray in skinnedFaces.items():
		# These MUST be arrays (not dicts) as order is important
		inGroupVerts = []
		inGroupVertArray.append([material_index, inGroupVerts])
		
		notInGroupVerts = []
		notInGroupVertArray.append([material_index, notInGroupVerts])

		material = obj.data.materials[material_index]
		fMaterial, texDimensions = \
			saveOrGetF3DMaterial(material, fModel, obj, drawLayer, convertTextureData)
		
		exportVertexColors = isLightingDisabled(material)
		convertInfo = LoopConvertInfo(uv_data, obj, exportVertexColors)
		for skinnedFace in skinnedFaceArray:
			for (face, loop) in skinnedFace.loopsInGroup:
				f3dVert = getF3DVert(loop, face, convertInfo, obj.data)
				if f3dVert not in inGroupVerts:
					inGroupVerts.append(f3dVert)
				loopDict[loop] = f3dVert
			for (face, loop) in skinnedFace.loopsNotInGroup:
				vert = obj.data.vertices[loop.vertex_index]
				if vert not in notInGroupBlenderVerts:
					notInGroupBlenderVerts.append(vert)
				f3dVert = getF3DVert(loop, face, convertInfo, obj.data)
				if f3dVert not in notInGroupVerts:
					notInGroupVerts.append(f3dVert)
				loopDict[loop] = f3dVert
	
	return inGroupVertArray, notInGroupVertArray, loopDict, notInGroupBlenderVerts

def getGroupVertCount(group):
	count = 0
	for material_index, vertData in group:
		count += len(vertData)
	return count

def saveSkinnedMeshByMaterial(skinnedFaces, fModel, name, obj, 
	currentMatrix, parentMatrix, namePrefix, infoDict, vertexGroup, drawLayer, convertTextureData):
	# We choose one or more loops per vert to represent a material from which 
	# texDimensions can be found, since it is required for UVs.
	uv_data = obj.data.uv_layers['UVMap'].data
	inGroupVertArray, notInGroupVertArray, loopDict, notInGroupBlenderVerts = \
		splitSkinnedFacesIntoTwoGroups(skinnedFaces, fModel, obj, uv_data, drawLayer, convertTextureData)

	notInGroupCount = getGroupVertCount(notInGroupVertArray)
	if notInGroupCount > fModel.f3d.vert_load_size - 2:
		highlightWeightErrors(obj, notInGroupBlenderVerts, 'VERT')
		raise VertexWeightError("Too many connecting vertices in skinned " +\
			"triangles for bone '" + vertexGroup + "'. Max is " + str(fModel.f3d.vert_load_size - 2) + \
			" on parent bone, currently at " + str(notInGroupCount) +\
			". Note that a vertex with different UVs/normals/materials in " +\
			"connected faces will count more than once. Try " +\
			"keeping UVs contiguous, and avoid using " +\
			"split normals.")
	
	# Load parent group vertices
	fSkinnedMesh = FMesh(toAlnum(namePrefix + \
			('_' if namePrefix != '' else '') + name) + '_skinned', fModel.DLFormat)

	# Load verts into buffer by material.
	# It seems like material setup must be done BEFORE triangles are drawn.
	# Because of this we cannot share verts between materials (?)
	curIndex = 0
	for material_index, vertData in notInGroupVertArray:
		material = obj.data.materials[material_index]
		checkForF3dMaterialInFaces(obj, material)
		if material.rdp_settings.set_rendermode:
			drawLayerKey = drawLayer
		else:
			drawLayerKey = None
		fMaterial, texDimensions = fModel.materials[(material, drawLayerKey)]
		isPointSampled = isTexturePointSampled(material)
		exportVertexColors = isLightingDisabled(material)

		skinnedTriGroup = fSkinnedMesh.tri_group_new(fMaterial)
		fSkinnedMesh.draw.commands.append(SPDisplayList(fMaterial.material))
		fSkinnedMesh.draw.commands.append(SPDisplayList(skinnedTriGroup.triList))
		skinnedTriGroup.triList.commands.append(
			SPVertex(skinnedTriGroup.vertexList, 
				len(skinnedTriGroup.vertexList.vertices), 
				len(vertData), curIndex))
		curIndex += len(vertData)

		for f3dVert in vertData:
			skinnedTriGroup.vertexList.vertices.append(convertVertexData(obj.data,
				f3dVert[0], f3dVert[1], f3dVert[2], texDimensions,
				parentMatrix, isPointSampled, exportVertexColors))
		
		skinnedTriGroup.triList.commands.append(SPEndDisplayList())
		if fMaterial.revert is not None:
			fSkinnedMesh.draw.commands.append(SPDisplayList(fMaterial.revert))

	# End skinned mesh vertices.
	fSkinnedMesh.draw.commands.append(SPEndDisplayList())

	fMesh = FMesh(toAlnum(namePrefix + \
			('_' if namePrefix != '' else '') + name) + '_mesh', fModel.DLFormat)

	# Load current group vertices, then draw commands by material
	existingVertData, matRegionDict = \
		convertVertDictToArray(notInGroupVertArray)
	for material_index, skinnedFaceArray in skinnedFaces.items():

		# We've already saved all materials, this just returns the existing ones.
		material = obj.data.materials[material_index]
		fMaterial, texDimensions = \
			saveOrGetF3DMaterial(material, fModel, obj, drawLayer, convertTextureData)
		isPointSampled = isTexturePointSampled(material)
		exportVertexColors = isLightingDisabled(material)

		triGroup = fMesh.tri_group_new(fMaterial)
		fMesh.draw.commands.append(SPDisplayList(fMaterial.material))
		fMesh.draw.commands.append(SPDisplayList(triGroup.triList))
		if fMaterial.revert is not None:
			fMesh.draw.commands.append(SPDisplayList(fMaterial.revert))

		convertInfo = LoopConvertInfo(uv_data, obj, exportVertexColors)
		saveTriangleStrip(
			[skinnedFace.bFace for skinnedFace in skinnedFaceArray],
			convertInfo, triGroup.triList, triGroup.vertexList, fModel.f3d, 
			texDimensions, parentMatrix, isPointSampled, exportVertexColors,
			copy.deepcopy(existingVertData), copy.deepcopy(matRegionDict),
			infoDict, obj.data)
	
	return FMeshGroup(toAlnum(namePrefix + \
			('_' if namePrefix != '' else '') + name), fMesh, fSkinnedMesh, fModel.DLFormat)

def writeDynamicMeshFunction(name, displayList):
	data = \
"""Gfx *{}(s32 callContext, struct GraphNode *node, UNUSED Mat4 *c) {
	struct GraphNodeGenerated *asmNode = (struct GraphNodeGenerated *) node;
    Gfx *displayListStart = NULL;
    if (callContext == GEO_CONTEXT_RENDER) {
        displayListStart = alloc_display_list({} * sizeof(*displayListStart));
        Gfx* glistp = displayListStart;
		{}
    }
    return displayListStart;
}""".format(name, str(len(displayList.commands)), displayList.to_c(False))

	return data