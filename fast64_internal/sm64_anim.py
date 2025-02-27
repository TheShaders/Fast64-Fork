import bpy
import mathutils
import math
import re
from .utility import *
from .sm64_constants import *
from math import pi
from .sm64_geolayout_classes import *
import os
import copy

sm64_anim_types = {'ROTATE', 'TRANSLATE'}

class SM64_Animation:
	def __init__(self, name):
		self.name = name
		self.header = None
		self.indices = SM64_ShortArray(name + '_indices', False)
		self.values = SM64_ShortArray(name + '_values', True)
	
	def get_ptr_offsets(self, isDMA):
		return [12, 16] if not isDMA else []

	def to_binary(self, segmentData, isDMA, startAddress):
		return self.header.to_binary(segmentData, isDMA, startAddress) + \
			self.indices.to_binary() + \
			self.values.to_binary()
	
	def to_c(self):
		return self.values.to_c() + '\n' +\
			self.indices.to_c() + '\n' +\
			self.header.to_c() + '\n'
		#return self.header.to_c() + '\n' +\
		#	self.indices.to_c() + '\n' +\
		#	self.values.to_c() + '\n'
	
	def to_c_def(self):
		return "extern const struct Animation *const " + self.name + '[];\n'

class SM64_ShortArray:
	def __init__(self, name, signed):
		self.name = name
		self.shortData = []
		self.signed = signed
	
	def to_binary(self):
		data = bytearray(0)
		for short in self.shortData:
			# All euler values have been pre-converted to positive values, so don't care about signed.
			data += short.to_bytes(2, 'big', signed = False)
		return data
	
	def to_c(self):
		data = 'static const ' + ('s' if self.signed else 'u') + \
			'16 ' + self.name + '[] = {\n\t'
		wrapCounter = 0
		for short in self.shortData:
			data += '0x' + format(short, '04X') + ', '
			wrapCounter += 1
			if wrapCounter > 8:
				data += '\n\t'
				wrapCounter = 0
		data += '\n};\n'
		return data

class SM64_AnimationHeader:
	def __init__(self, name, repetitions, marioYOffset, frameInterval, 
		nodeCount, transformValuesStart, transformIndicesStart, animSize):
		self.name = name
		self.repetitions = repetitions
		self.marioYOffset = marioYOffset
		self.frameInterval = frameInterval
		self.nodeCount = nodeCount
		self.transformValuesStart = transformValuesStart
		self.transformIndicesStart = transformIndicesStart
		self.animSize = animSize # DMA animations only
		
		self.transformIndices = []

	# presence of segmentData indicates DMA.
	def to_binary(self, segmentData, isDMA, startAddress):
		if isDMA:
			transformValuesStart = self.transformValuesStart
			transformIndicesStart = self.transformIndicesStart
		else:
			transformValuesStart = self.transformValuesStart + startAddress
			transformIndicesStart = self.transformIndicesStart + startAddress

		data = bytearray(0)
		data.extend(self.repetitions.to_bytes(2, byteorder='big'))
		data.extend(self.marioYOffset.to_bytes(2, byteorder='big')) # y offset, only used for mario
		data.extend([0x00, 0x00]) # unknown, common with secondary anims, variable length animations?
		data.extend(int(round(self.frameInterval[0])).to_bytes(2, byteorder='big'))
		data.extend(int(round(self.frameInterval[1] - 1)).to_bytes(2, byteorder='big'))
		data.extend(self.nodeCount.to_bytes(2, byteorder='big'))
		if not isDMA:
			data.extend(encodeSegmentedAddr(transformValuesStart, segmentData))
			data.extend(encodeSegmentedAddr(transformIndicesStart, segmentData))
			data.extend(bytearray([0x00] * 6))
		else:
			data.extend(transformValuesStart.to_bytes(4, byteorder='big'))
			data.extend(transformIndicesStart.to_bytes(4, byteorder='big'))
			data.extend(self.animSize.to_bytes(4, byteorder='big'))
			data.extend(bytearray([0x00] * 2))
		return data

	def to_c(self):
		data = 'static const struct Animation ' + self.name + ' = {\n' +\
			'\t' + str(self.repetitions) + ',\n' + \
			'\t' + str(self.marioYOffset) + ',\n' + \
			'\t0,\n' + \
			'\t' + str(int(round(self.frameInterval[0]))) + ',\n' + \
			'\t' + str(int(round(self.frameInterval[1] - 1))) + ',\n' + \
			'\tANIMINDEX_NUMPARTS(' + self.name + '_indices),\n' + \
			'\t' + self.name + '_values,\n' + \
			'\t' + self.name + '_indices,\n' + \
			'\t0,\n' + \
			'};\n'
		return data

class SM64_AnimIndexNode:
	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z

class SM64_AnimIndex:
	def __init__(self, numFrames, startOffset):
		self.startOffset = startOffset
		self.numFrames = numFrames

def getLastKeyframeTime(keyframes):
	last = keyframes[0].co[0]
	for keyframe in keyframes:
		if keyframe.co[0] > last:
			last = keyframe.co[0]
	return last


# add definition to groupN.h
# add data/table includes to groupN.c (bin_id?)
# add data/table files
def exportAnimationC(armatureObj, loopAnim, dirPath, dirName,
	customExport, headerType, levelName):
	dirPath, texDir = getExportDir(customExport, dirPath, headerType, 
		levelName, '', dirName)

	modelAnim = exportAnimationCommon(armatureObj, loopAnim, dirName + "_anim")
	animName = armatureObj.animation_data.action.name

	geoDirPath = os.path.join(dirPath, toAlnum(dirName))
	if not os.path.exists(geoDirPath):
		os.mkdir(geoDirPath)

	animDirPath = os.path.join(geoDirPath, 'anims')
	if not os.path.exists(animDirPath):
		os.mkdir(animDirPath)

	animsName = dirName + '_anims'
	animFileName = 'anim_' + toAlnum(animName) + '.inc.c'
	animPath = os.path.join(animDirPath, animFileName)

	data = modelAnim.to_c()
	outFile = open(animPath, 'w', newline='\n')
	outFile.write(data)
	outFile.close()

	headerPath = os.path.join(geoDirPath, 'anim_header.h')
	headerFile = open(headerPath, 'w', newline='\n')
	headerFile.write('extern const struct Animation *const ' + animsName + '[];\n')
	headerFile.close()

	# write to data.inc.c
	dataFilePath = os.path.join(animDirPath, 'data.inc.c')
	if not os.path.exists(dataFilePath):
		dataFile = open(dataFilePath, 'w', newline='\n')
		dataFile.close()
	writeIfNotFound(dataFilePath, '#include "' + animFileName + '"\n', '')

	# write to table.inc.c
	tableFilePath = os.path.join(animDirPath, 'table.inc.c')
	if not os.path.exists(tableFilePath):
		tableFile = open(tableFilePath, 'w', newline='\n')
		tableFile.write('const struct Animation *const ' + \
			animsName + '[] = {\n\tNULL,\n};\n')
		tableFile.close()
	writeIfNotFound(tableFilePath, '\t&' + modelAnim.name + ',\n', '\tNULL,\n};')

	# if not customExport:
	# 	if headerType == 'Actor':
	# 		groupPathC = os.path.join(dirPath, groupName + ".c")
	# 		groupPathH = os.path.join(dirPath, groupName + ".h")

	# 		writeIfNotFound(groupPathC, '\n#include "' + dirName + '/anims/data.inc.c"', '')
	# 		writeIfNotFound(groupPathC, '\n#include "' + dirName + '/anims/table.inc.c"', '')
	# 		writeIfNotFound(groupPathH, '\n#include "' + dirName + '/anim_header.h"', '#endif')
	# 	elif headerType == 'Level':
	# 		groupPathC = os.path.join(dirPath, "leveldata.c")
	# 		groupPathH = os.path.join(dirPath, "header.h")

	# 		writeIfNotFound(groupPathC, '\n#include "levels/' + levelName + '/' + dirName + '/anims/data.inc.c"', '')
	# 		writeIfNotFound(groupPathC, '\n#include "levels/' + levelName + '/' + dirName + '/anims/table.inc.c"', '')
	# 		writeIfNotFound(groupPathH, '\n#include "levels/' + levelName + '/' + dirName + '/anim_header.h"', '\n#endif')

def exportAnimationCommon(armatureObj, loopAnim, name):
	if armatureObj.animation_data is None or \
		armatureObj.animation_data.action is None:
		raise PluginError("No active animation selected.")
	anim = armatureObj.animation_data.action
	modelAnim = ModelAnim(name + '_' + anim.name)
		
	frameInterval = [0,0]

	# frame_start is minimum 0
	frameInterval[0] = max(bpy.context.scene.frame_start,
		int(round(anim.frame_range[0])))

	frameInterval[1] = \
		max(min(bpy.context.scene.frame_end, 
			int(round(anim.frame_range[1]))), frameInterval[0]) + 1
	
	translationData, rotationData, scaleData = convertAnimationData(anim, armatureObj, frameInterval[1])

	modelAnim.loop = loopAnim

	for i in range(len(translationData)):
		modelAnim.addBoneData([
			translationData[i][0], translationData[i][1], translationData[i][2],
			rotationData[i][0], rotationData[i][1], rotationData[i][2],
			scaleData[i][0], scaleData[i][1], scaleData[i][2]])
	
	return modelAnim
	
def saveQuaternionFrame(frameData, rotation):
	for i in range(3):
		field = rotation.to_euler()[i]
		value = (math.degrees(field) % 360 ) / 360
		frameData[i].append(min(int(round(value * (2**16 - 1))), 2**16 - 1))

def removeTrailingFrames(frameData):
	for i in range(3):
		if len(frameData[i]) < 2:
			continue
		lastUniqueFrame = len(frameData[i]) - 1
		while lastUniqueFrame > 0:
			if frameData[i][lastUniqueFrame] == \
				frameData[i][lastUniqueFrame - 1]:
				lastUniqueFrame -= 1
			else:
				break
		frameData[i] = frameData[i][:lastUniqueFrame + 1]

def convertSignedToUnsigned(val):
	return int.from_bytes(val.to_bytes(
			2, 'big', signed = True), 'big', signed = False)

def saveTranslationFrame(frameData, translation):
	for i in range(3):
		frameData[i].append(min(convertSignedToUnsigned(int(round(translation[i] * bpy.context.scene.blenderToN64Scale))),
			2**16 - 1))

def saveScaleFrame(frameData, scale):
	for i in range(3):
		frameData[i].append(min(convertSignedToUnsigned(int(round(scale[i] * 256))),
			2**16 - 1))

def convertAnimationData(anim, armatureObj, frameEnd):
	bonesToProcess = findStartBones(armatureObj)
	currentBone = armatureObj.data.bones[bonesToProcess[0]]
	animBones = []

	# Get animation bones in order
	while len(bonesToProcess) > 0:
		boneName = bonesToProcess[0]
		currentBone = armatureObj.data.bones[boneName]
		currentPoseBone = armatureObj.pose.bones[boneName]
		bonesToProcess = bonesToProcess[1:]

		#if currentBone.geo_cmd == 'DisplayListWithOffset':
		animBones.append(boneName)

		# Traverse children in alphabetical order.
		childrenNames = sorted([bone.name for bone in currentBone.children])
		bonesToProcess = childrenNames + bonesToProcess
	
	# list of boneFrameData, which is [[x frames], [y frames], [z frames]]
	translationData = [[[],[],[]] for _ in range(len(animBones))]
	rotationData = [[[],[],[]] for _ in range(len(animBones))]
	scaleData = [[[],[],[]] for _ in range(len(animBones))]

	for frame in range(frameEnd):
		bpy.context.scene.frame_set(frame)
		for boneIndex in range(len(animBones)):
			boneName = animBones[boneIndex]
			currentBone = armatureObj.data.bones[boneName]
			currentPoseBone = armatureObj.pose.bones[boneName]


			decomposedTranslation = currentPoseBone.matrix.decompose()[0]
			decomposedRootTranslation = currentBone.matrix_local.decompose()[0]
			decomposedScale = currentPoseBone.matrix.decompose()[2]
			decomposedRootScale = currentBone.matrix.to_4x4().decompose()[2]

			if boneIndex == 0 and frame == 0:
				print(boneName)
				print(decomposedTranslation)
				print(decomposedRootTranslation)
				print(decomposedScale)
				print(decomposedRootScale)

			# Hacky solution to handle Z-up to Y-up conversion
			translationValue = mathutils.Quaternion((1, 0, 0), math.radians(-90.0)) @ \
				(decomposedTranslation - decomposedRootTranslation)
			# Swap Y and Z
			scaleValue = mathutils.Vector((decomposedScale[0] / decomposedRootScale[0], decomposedScale[2] / decomposedRootScale[2], decomposedScale[1] / decomposedRootScale[1]))

			
			rotationValue = \
				(currentBone.matrix.to_4x4().inverted() @ \
				currentPoseBone.matrix).to_quaternion()
			if currentBone.parent is not None:
				rotationValue = (
					currentBone.matrix.to_4x4().inverted() @ currentPoseBone.parent.matrix.inverted() @ \
					currentPoseBone.matrix).to_quaternion()
				decomposedParentTranslation = currentPoseBone.parent.matrix.decompose()[0]
				decomposedParentRootTranslation = currentBone.parent.matrix_local.decompose()[0]
				translationValue = mathutils.Quaternion((1, 0, 0), math.radians(-90.0)) @ \
					(decomposedTranslation - decomposedRootTranslation - (decomposedParentTranslation - decomposedParentRootTranslation))
			
			saveTranslationFrame(translationData[boneIndex], translationValue)
			saveQuaternionFrame(rotationData[boneIndex], rotationValue)
			saveScaleFrame(scaleData[boneIndex], scaleValue)
	return translationData, rotationData, scaleData

def getNextBone(boneStack, armatureObj):
	if len(boneStack) == 0:
		raise PluginError("More bones in animation than on armature.")
	bone = armatureObj.data.bones[boneStack[0]]
	boneStack = boneStack[1:]
	boneStack = sorted([child.name for child in bone.children]) + boneStack

	# Only return 0x13 bone
	while armatureObj.data.bones[bone.name].geo_cmd != 'DisplayListWithOffset':
		if len(boneStack) == 0:
			raise PluginError("More bones in animation than on armature.")
		bone = armatureObj.data.bones[boneStack[0]]
		boneStack = boneStack[1:]
		boneStack = sorted([child.name for child in bone.children]) + boneStack
	
	return bone, boneStack

def importAnimationToBlender(romfile, startAddress, armatureObj, segmentData, isDMA):
	boneStack = findStartBones(armatureObj)
	startBoneName = boneStack[0]
	if armatureObj.data.bones[startBoneName].geo_cmd != 'DisplayListWithOffset':
		startBone, boneStack = getNextBone(boneStack, armatureObj)
		startBoneName = startBone.name
		boneStack = [startBoneName] + boneStack

	animationHeader, armatureFrameData = \
		readAnimation('sm64_anim', romfile, startAddress, segmentData, isDMA)

	if len(armatureFrameData) > len(armatureObj.data.bones) + 1:
		raise PluginError('More bones in animation than on armature.')

	#bpy.context.scene.render.fps = 30
	bpy.context.scene.frame_end = animationHeader.frameInterval[1]
	anim = bpy.data.actions.new("sm64_anim")

	isRootTranslation = True
	# boneFrameData = [[x keyframes], [y keyframes], [z keyframes]]
	# len(armatureFrameData) should be = number of bones
	# property index = 0,1,2 (aka x,y,z)
	for boneFrameData in armatureFrameData:
		if isRootTranslation:
			for propertyIndex in range(3):
				fcurve = anim.fcurves.new(
					data_path = 'pose.bones["' + startBoneName + '"].location',
					index = propertyIndex,
					action_group = startBoneName)
				for frame in range(len(boneFrameData[propertyIndex])):
					fcurve.keyframe_points.insert(frame, boneFrameData[propertyIndex][frame])
			isRootTranslation = False
		else:
			bone, boneStack = getNextBone(boneStack, armatureObj)
			for propertyIndex in range(3):
				fcurve = anim.fcurves.new(
					data_path = 'pose.bones["' + bone.name + '"].rotation_euler', 
					index = propertyIndex,
					action_group = bone.name)
				for frame in range(len(boneFrameData[propertyIndex])):
					fcurve.keyframe_points.insert(frame, boneFrameData[propertyIndex][frame])

	if armatureObj.animation_data is None:
		armatureObj.animation_data_create()
	armatureObj.animation_data.action = anim
		
def readAnimation(name, romfile, startAddress, segmentData, isDMA):
	animationHeader = readAnimHeader(name, romfile, startAddress, segmentData, isDMA)
	
	print("Frames: " + str(animationHeader.frameInterval[1]) + " / Nodes: " + str(animationHeader.nodeCount))

	animationHeader.transformIndices = readAnimIndices(
		romfile, animationHeader.transformIndicesStart, animationHeader.nodeCount)

	armatureFrameData = [] #list of list of frames

	# sm64 space -> blender space -> pose space
	# BlenderToSM64: YZX (set rotation mode of bones)
	# SM64toBlender: ZXY (set anim keyframes and model armature)
	# new bones should extrude in +Y direction

	# handle root translation
	boneFrameData = [[],[],[]]
	rootIndexNode = animationHeader.transformIndices[0]
	boneFrameData[0] = [n for n in getKeyFramesTranslation(romfile, animationHeader.transformValuesStart, rootIndexNode.x)]
	boneFrameData[1] = [n for n in getKeyFramesTranslation(romfile, animationHeader.transformValuesStart, rootIndexNode.y)]
	boneFrameData[2] = [n for n in getKeyFramesTranslation(romfile, animationHeader.transformValuesStart, rootIndexNode.z)]
	armatureFrameData.append(boneFrameData)

	# handle rotations
	for boneIndexNode in animationHeader.transformIndices[1:]:
		boneFrameData = [[],[],[]]

		# Transforming SM64 space to Blender space
		boneFrameData[0] = [n for n in \
			getKeyFramesRotation(romfile, animationHeader.transformValuesStart, boneIndexNode.x)]
		boneFrameData[1] = [n for n in \
			getKeyFramesRotation(romfile, animationHeader.transformValuesStart, boneIndexNode.y)]
		boneFrameData[2] = [n for n in \
			getKeyFramesRotation(romfile, animationHeader.transformValuesStart, boneIndexNode.z)]

		armatureFrameData.append(boneFrameData)

	return (animationHeader, armatureFrameData)

def getKeyFramesRotation(romfile, transformValuesStart, boneIndex):
	ptrToValue = transformValuesStart + boneIndex.startOffset
	romfile.seek(ptrToValue)

	keyframes = []
	for frame in range(boneIndex.numFrames):
		romfile.seek(ptrToValue + frame * 2)
		value = int.from_bytes(romfile.read(2), 'big') * 360 / (2**16)
		keyframes.append(math.radians(value))

	return keyframes

def getKeyFramesTranslation(romfile, transformValuesStart, boneIndex):
	ptrToValue = transformValuesStart + boneIndex.startOffset
	romfile.seek(ptrToValue)

	keyframes = []
	for frame in range(boneIndex.numFrames):
		romfile.seek(ptrToValue + frame * 2)
		keyframes.append(int.from_bytes(romfile.read(2), 'big', signed = True) /\
			bpy.context.scene.blenderToN64Scale)

	return keyframes

def readAnimHeader(name, romfile, startAddress, segmentData, isDMA):
	frameInterval = [0,0]

	romfile.seek(startAddress + 0x00)
	numRepeats = int.from_bytes(romfile.read(2), 'big')

	romfile.seek(startAddress + 0x02)
	marioYOffset = int.from_bytes(romfile.read(2), 'big')

	romfile.seek(startAddress + 0x06)
	frameInterval[0] = int.from_bytes(romfile.read(2), 'big')

	romfile.seek(startAddress + 0x08)
	frameInterval[1] = int.from_bytes(romfile.read(2), 'big')

	romfile.seek(startAddress + 0x0A)
	numNodes = int.from_bytes(romfile.read(2), 'big')

	romfile.seek(startAddress + 0x0C)
	transformValuesOffset = int.from_bytes(romfile.read(4), 'big')
	if isDMA:	
		transformValuesStart = startAddress + transformValuesOffset
	else:
		transformValuesStart = decodeSegmentedAddr(
			transformValuesOffset.to_bytes(4, byteorder='big'), segmentData)

	romfile.seek(startAddress + 0x10)
	transformIndicesOffset = int.from_bytes(romfile.read(4), 'big')
	if isDMA:
		transformIndicesStart = startAddress + transformIndicesOffset
	else:
		transformIndicesStart = decodeSegmentedAddr(
			transformIndicesOffset.to_bytes(4, byteorder='big'), segmentData)

	romfile.seek(startAddress + 0x14)
	animSize = int.from_bytes(romfile.read(4), 'big')

	return SM64_AnimationHeader(name, numRepeats, marioYOffset, frameInterval, numNodes, 
		transformValuesStart, transformIndicesStart, animSize)

def readAnimIndices(romfile, ptrAddress, nodeCount):
	indices = []

	# Handle root transform
	rootPosIndex = readTransformIndex(romfile, ptrAddress)
	indices.append(rootPosIndex)

	# Handle rotations
	for i in range(nodeCount):
		rotationIndex = readTransformIndex(romfile, ptrAddress + (i+1) * 12)
		indices.append(rotationIndex)

	return indices

def readTransformIndex(romfile, startAddress):
	x = readValueIndex(romfile, startAddress + 0)
	y = readValueIndex(romfile, startAddress + 4)
	z = readValueIndex(romfile, startAddress + 8)

	return SM64_AnimIndexNode(x, y, z)

def readValueIndex(romfile, startAddress):
	romfile.seek(startAddress)
	numFrames = int.from_bytes(romfile.read(2), 'big')
	romfile.seek(startAddress + 2)

	# multiply 2 because value is the index in array of shorts (???)
	startOffset = int.from_bytes(romfile.read(2), 'big') * 2
	print(str(hex(startAddress)) + ": " + str(numFrames) + " " + str(startOffset))
	return SM64_AnimIndex(numFrames, startOffset)

def writeAnimation(romfile, startAddress, segmentData):
	pass

def writeAnimHeader(romfile, startAddress, segmentData):
	pass