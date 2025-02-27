import sys
import tempfile
import copy
import shutil
import bpy
import traceback
import os
from pathlib import Path
from .fast64_internal import *

import cProfile
import pstats

# info about add on
bl_info = {
	"name": "Fast64 Fork",
	"category": "Object",
	"blender": (2, 82, 0),
	}

axis_enums = [	
	('X', 'X', 'X'), 
	('Y', 'Y', 'Y'), 
	('-X', '-X', '-X'),
	('-Y', '-Y', '-Y'),
]

enumExportType = [
	('C', 'C', 'C'),
	('Binary', 'Binary', 'Binary'),
	('Insertable Binary', 'Insertable Binary', 'Insertable Binary')
]

enumHUDExportLocation = [
	('HUD', 'HUD', 'Exports to src/game/hud.c'),
	('Menu', 'Menu', 'Exports to src/game/ingame_menu.c')
]

# filepath, function to insert before
enumHUDPaths = {
	"HUD" : ('src/game/hud.c', 'void render_hud(void)'),
	'Menu' : ('src/game/ingame_menu.c', 's16 render_menus_and_dialogs()'),
}

enumExportHeaderType = [
	#('None', 'None', 'Headers are not written'),
	('Actor', 'Actor Data', 'Headers are written to a group in assets/'),
	('Level', 'Level Data', 'Headers are written to a specific level in levels/')
]

panelSeparatorSize = 5

def checkExpanded(filepath):
	size = os.path.getsize(filepath)
	if size < 9000000: # check if 8MB
		raise PluginError("ROM at " + filepath + " is too small. You may be using an unexpanded ROM. You can expand a ROM by opening it in SM64 Editor or ROM Manager.")

def getPathAndLevel(customExport, exportPath, levelName, levelOption):
	if customExport:
		exportPath = bpy.path.abspath(exportPath)
		levelName = levelName
	else:
		exportPath = bpy.path.abspath(bpy.context.scene.decompPath)
		if levelOption == 'custom':
			levelName = levelName
		else:
			levelName = levelOption
	return exportPath, levelName

class ArmatureApplyWithMesh(bpy.types.Operator):
	# set bl_ properties
	bl_description = 'Applies current pose as default pose. Useful for ' + \
		"rigging an armature that is not in T/A pose. Note that when using " +\
		" with an SM64 armature, you must revert to the default pose after " +\
		"skinning."
	bl_idname = 'object.armature_apply_w_mesh'
	bl_label = "Apply As Rest Pose"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		try:
			if context.mode != 'OBJECT' and context.mode != 'POSE':
				raise PluginError("Operator can only be used in object or pose mode.")
			elif context.mode == 'POSE':
				bpy.ops.object.mode_set(mode = "OBJECT")

			if len(context.selected_objects) == 0:
				raise PluginError("Armature not selected.")
			elif type(context.selected_objects[0].data) is not\
				bpy.types.Armature:
				raise PluginError("Armature not selected.")
			
			armatureObj = context.selected_objects[0]
			for child in armatureObj.children:
				if type(child.data) is not bpy.types.Mesh:
					continue
				armatureModifier = None
				for modifier in child.modifiers:
					if isinstance(modifier, bpy.types.ArmatureModifier):
						armatureModifier = modifier
				if armatureModifier is None:
					continue
				print(armatureModifier.name)
				bpy.ops.object.select_all(action = "DESELECT")
				context.view_layer.objects.active = child
				bpy.ops.object.modifier_copy(modifier=armatureModifier.name)
				print(len(child.modifiers))
				bpy.ops.object.modifier_apply(modifier=armatureModifier.name)

			bpy.ops.object.select_all(action = "DESELECT")
			context.view_layer.objects.active = armatureObj
			bpy.ops.object.mode_set(mode = "POSE")
			bpy.ops.pose.armature_apply()
		except Exception as e:
			raisePluginError(self, e)
			return {"CANCELLED"}

		self.report({'INFO'}, 'Applied armature with mesh.')
		return {'FINISHED'} # must return a set

class AddBoneGroups(bpy.types.Operator):
	# set bl_ properties
	bl_description = 'Add bone groups respresenting other node types in ' +\
		'SM64 geolayouts (ex. Shadow, Switch, Function).'
	bl_idname = 'object.add_bone_groups'
	bl_label = "Add Bone Groups"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		try:
			if context.mode != 'OBJECT' and context.mode != 'POSE':
				raise PluginError("Operator can only be used in object or pose mode.")
			elif context.mode == 'POSE':
				bpy.ops.object.mode_set(mode = "OBJECT")

			if len(context.selected_objects) == 0:
				raise PluginError("Armature not selected.")
			elif type(context.selected_objects[0].data) is not\
				bpy.types.Armature:
				raise PluginError("Armature not selected.")
			
			armatureObj = context.selected_objects[0]
			createBoneGroups(armatureObj)
		except Exception as e:
			raisePluginError(self, e)
			return {"CANCELLED"}

		self.report({'INFO'}, 'Created bone groups.')
		return {'FINISHED'} # must return a set

class N64_AddF3dMat(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.add_f3d_mat'
	bl_label = "Add Fast3D Material"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		try:
			if context.mode != 'OBJECT':
				raise PluginError("Operator can only be used in object mode.")
			
			if len(context.selected_objects) == 0:
				raise PluginError("Mesh not selected.")
			elif type(context.selected_objects[0].data) is not\
				bpy.types.Mesh:
				raise PluginError("Mesh not selected.")
			
			obj = context.selected_objects[0]
			createF3DMat(obj)
		except Exception as e:
			raisePluginError(self, e)
			return {"CANCELLED"}

		self.report({'INFO'}, 'Created F3D material.')
		return {'FINISHED'} # must return a set

# See SM64GeoLayoutPtrsByLevels.txt by VLTone
class SM64_ImportGeolayout(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.sm64_import_geolayout'
	bl_label = "Import Geolayout"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		romfileSrc = None
		try:
			geoImportAddr = context.scene.geoImportAddr
			generateArmature = context.scene.generateArmature
			levelGeoImport = context.scene.levelGeoImport
			importRom = context.scene.importRom
			ignoreSwitch = context.scene.ignoreSwitch

			#finalTransform = mathutils.Matrix.Rotation(math.radians(-90), 4, 'X')
			finalTransform = mathutils.Matrix.Identity(4)
			if context.mode != 'OBJECT':
				raise PluginError("Operator can only be used in object mode.")
		except Exception as e:
			raisePluginError(self, e)
			return {'CANCELLED'}
		try:
			romfileSrc = open(bpy.path.abspath(importRom), 'rb')
			checkExpanded(bpy.path.abspath(importRom))

			armatureObj = None

			# Get segment data
			levelParsed = parseLevelAtPointer(romfileSrc, 
				level_pointers[levelGeoImport])
			segmentData = levelParsed.segmentData
			geoStart = int(geoImportAddr, 16)
			if context.scene.geoIsSegPtr:
				geoStart = decodeSegmentedAddr(
					geoStart.to_bytes(4, 'big'), segmentData)

			# Armature mesh groups includes armatureObj.
			armatureMeshGroups, armatureObj = parseGeoLayout(romfileSrc, 
				geoStart,
			 	context.scene, segmentData, 
				finalTransform, generateArmature, 
				ignoreSwitch, True, context.scene.f3d_type, 
				context.scene.isHWv1)
			romfileSrc.close()

			bpy.ops.object.select_all(action = 'DESELECT')
			if armatureObj is not None:
				for armatureMeshGroup in armatureMeshGroups:
					armatureMeshGroup[0].select_set(True)
				doRotation(math.radians(-90), 'X')

				for armatureMeshGroup in armatureMeshGroups:
					bpy.ops.object.select_all(action = 'DESELECT')
					armatureMeshGroup[0].select_set(True)
					bpy.context.view_layer.objects.active = armatureMeshGroup[0]
					bpy.ops.object.make_single_user(obdata = True)
					bpy.ops.object.transform_apply(location = False, 
						rotation = True, scale = False, properties =  False)
			else:
				doRotation(math.radians(-90), 'X')
			bpy.ops.object.select_all(action = 'DESELECT')
			#objs[-1].select_set(True)

			self.report({'INFO'}, 'Generic import succeeded.')
			return {'FINISHED'} # must return a set

		except Exception as e:
			if context.mode != 'OBJECT':
				bpy.ops.object.mode_set(mode = 'OBJECT')
			
			if romfileSrc is not None:
				romfileSrc.close()
			raisePluginError(self, e)
			return {'CANCELLED'} # must return a set

class SM64_ImportGeolayoutPanel(bpy.types.Panel):
	bl_idname = "SM64_PT_import_geolayout"
	bl_label = "SM64 Geolayout Importer"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsGeoI = col.operator(SM64_ImportGeolayout.bl_idname)

		#col.prop(context.scene, 'rotationOrder')
		#col.prop(context.scene, 'rotationAxis')
		#col.prop(context.scene, 'rotationAngle')
		prop_split(col, context.scene, 'geoImportAddr', 'Start Address')
		col.prop(context.scene, 'geoIsSegPtr')
		col.prop(context.scene, 'levelGeoImport')
		col.prop(context.scene, 'generateArmature')
		col.prop(context.scene, 'ignoreSwitch')
		if not context.scene.ignoreSwitch:
			boxLayout = col.box()
			boxLayout.label(text = "WARNING: May take a long time.")
			boxLayout.label(text = "Switch nodes won't be setup.")
		col.box().label(text = "Only Fast3D mesh importing allowed.")
		for i in range(panelSeparatorSize):
			col.separator()

class Fork_ExportModelFromMesh(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.fast64_fork_export_geolayout_object'
	bl_label = "Export Model from Mesh"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		romfileOutput = None
		tempROM = None
		try:
			obj = None
			if context.mode != 'OBJECT':
				raise PluginError("Operator can only be used in object mode.")
			if len(context.selected_objects) == 0:
				raise PluginError("Object not selected.")
			obj = context.active_object
			if type(obj.data) is not bpy.types.Mesh and \
				not (obj.data is None and (obj.sm64_obj_type == 'None' or obj.sm64_obj_type == 'Switch')):
				raise PluginError("Selected object must be a mesh or an empty with the \"None\" or \"Switch\" type.")
			#if context.scene.saveCameraSettings and \
			#	context.scene.levelCamera is None:
			#	raise PluginError("Cannot save camera settings with no camera provided.")
			#levelCamera = context.scene.levelCamera if \
			#	context.scene.saveCameraSettings else None

			scaleValue = bpy.context.scene.blenderToN64Scale
			finalTransform = mathutils.Matrix.Diagonal(mathutils.Vector((
				scaleValue, scaleValue, scaleValue))).to_4x4()
		except Exception as e:
			raisePluginError(self, e)
			return {'CANCELLED'}

		try:
			# Rotate all armatures 90 degrees
			applyRotation([obj], math.radians(-90), 'X')

			exportPath, levelName = getPathAndLevel(context.scene.geoCustomExport, 
				context.scene.geoExportPath, context.scene.geoLevelName, 
				context.scene.geoLevelOption)
			if not context.scene.geoCustomExport:
				applyBasicTweaks(exportPath)
			exportModelFromMesh(obj, finalTransform,
				context.scene.f3d_type, context.scene.isHWv1,
				exportPath,
				bpy.context.scene.geoTexDir,
				bpy.context.scene.geoSaveTextures or bpy.context.scene.ignoreTextureRestrictions,
				bpy.context.scene.geoSeparateTextureDef,
				None, bpy.context.scene.geoGroupName, 
				context.scene.geoExportHeaderType,
				context.scene.geoName, context.scene.geoStructName, levelName, context.scene.geoCustomExport, "Static")
			self.report({'INFO'}, 'Success!')
			
			applyRotation([obj], math.radians(90), 'X')
			return {'FINISHED'} # must return a set

		except Exception as e:
			if context.mode != 'OBJECT':
				bpy.ops.object.mode_set(mode = 'OBJECT')

			applyRotation([obj], math.radians(90), 'X')

			raisePluginError(self, e)
			return {'CANCELLED'} # must return a set

class Fork_ExportModelFromArmature(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.fast64_fork_export_geolayout_armature'
	bl_label = "Export Model from Armature"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		romfileOutput = None
		tempROM = None
		try:
			armatureObj = None
			if context.mode != 'OBJECT':
				raise PluginError("Operator can only be used in object mode.")
			if len(context.selected_objects) == 0:
				raise PluginError("Armature not selected.")
			armatureObj = context.active_object
			if type(armatureObj.data) is not bpy.types.Armature:
				raise PluginError("Armature not selected.")

			if len(armatureObj.children) == 0 or \
				not isinstance(armatureObj.children[0].data, bpy.types.Mesh):
				raise PluginError("Armature does not have any mesh children, or " +\
					'has a non-mesh child.')
			#if context.scene.saveCameraSettings and \
			#	context.scene.levelCamera is None:
			#	raise PluginError("Cannot save camera settings with no camera provided.")
			#levelCamera = context.scene.levelCamera if \
			#	context.scene.saveCameraSettings else None

			obj = armatureObj.children[0]
			scaleValue = bpy.context.scene.blenderToN64Scale
			finalTransform = mathutils.Matrix.Diagonal(mathutils.Vector((
				scaleValue, scaleValue, scaleValue))).to_4x4()

			# get all switch option armatures as well
			linkedArmatures = [armatureObj]
			getAllArmatures(armatureObj, linkedArmatures)

			linkedArmatureDict = {}

			for linkedArmature in linkedArmatures:
				# IMPORTANT: Do this BEFORE rotation
				optionObjs = []
				for childObj in linkedArmature.children:
					if isinstance(childObj.data, bpy.types.Mesh):
						optionObjs.append(childObj)
				if len(optionObjs) > 1:
					raise PluginError('Error: ' + linkedArmature.name +\
						' has more than one mesh child.')
				elif len(optionObjs) < 1:
					raise PluginError('Error: ' + linkedArmature.name +\
						' has no mesh children.')
				linkedMesh = optionObjs[0]
				prepareGeolayoutExport(linkedArmature, linkedMesh)
				linkedArmatureDict[linkedArmature] = linkedMesh
		except Exception as e:
			raisePluginError(self, e)
			return {'CANCELLED'}

		try:
			# Rotate all armatures 90 degrees
			applyRotation([armatureObj] + linkedArmatures, 
				math.radians(-90), 'X')

			# You must ALSO apply object rotation after armature rotation.
			bpy.ops.object.select_all(action = "DESELECT")
			for linkedArmature, linkedMesh in linkedArmatureDict.items():
				linkedMesh.select_set(True)
			obj.select_set(True)
			bpy.context.view_layer.objects.active = obj
			bpy.ops.object.transform_apply(location = False, rotation = True,
				scale = True, properties =  False)
			exportPath, levelName = getPathAndLevel(context.scene.geoCustomExport, 
				context.scene.geoExportPath, context.scene.geoLevelName, 
				context.scene.geoLevelOption)

			if not context.scene.geoCustomExport:
				applyBasicTweaks(exportPath)
			exportGeolayoutArmatureC(armatureObj, obj, finalTransform,
				context.scene.f3d_type, context.scene.isHWv1,
				exportPath,
				bpy.context.scene.geoTexDir,
				bpy.context.scene.geoSaveTextures or bpy.context.scene.ignoreTextureRestrictions,
				bpy.context.scene.geoSeparateTextureDef,
				None, bpy.context.scene.geoGroupName, context.scene.geoExportHeaderType,
				context.scene.geoName, context.scene.geoStructName, levelName, context.scene.geoCustomExport, "Static")
			self.report({'INFO'}, 'Success!')

			applyRotation([armatureObj] + linkedArmatures, 
				math.radians(90), 'X')

			return {'FINISHED'} # must return a set

		except Exception as e:
			if context.mode != 'OBJECT':
				bpy.ops.object.mode_set(mode = 'OBJECT')
			
			applyRotation([armatureObj] + linkedArmatures, 
				math.radians(90), 'X')

			if armatureObj is not None:
				armatureObj.select_set(True)
				context.view_layer.objects.active = armatureObj
			raisePluginError(self, e)
			return {'CANCELLED'} # must return a set

class Fork_ModelExportPanel(bpy.types.Panel):
	bl_idname = "FAST64_FORK_PT_export_geolayout"
	bl_label = "Model Exporter"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsGeoE = col.operator(Fork_ExportModelFromArmature.bl_idname)
		propsGeoE = col.operator(Fork_ExportModelFromMesh.bl_idname)

		if not bpy.context.scene.ignoreTextureRestrictions:
			col.prop(context.scene, 'geoSaveTextures')
			if context.scene.geoSaveTextures:
				if context.scene.geoCustomExport:
					prop_split(col, context.scene, 'geoTexDir', 'Texture Include Path')	
				col.prop(context.scene, 'geoSeparateTextureDef')
		
		col.prop(context.scene, 'geoCustomExport')
		if context.scene.geoCustomExport:
			col.prop(context.scene, 'geoExportPath')
			prop_split(col, context.scene, 'geoName', 'Folder Name')
			prop_split(col, context.scene, 'geoStructName', 'Model Name')
			customExportWarning(col)
		else:
			prop_split(col, context.scene, 'geoExportHeaderType', 'Export Type')
			if context.scene.geoExportHeaderType == 'Level':
				prop_split(col, context.scene, 'geoLevelOption', 'Level')
				if context.scene.geoLevelOption == 'custom':
					prop_split(col, context.scene, 'geoLevelName', 'Level Name')
			prop_split(col, context.scene, 'geoName', 'Folder Name')
			prop_split(col, context.scene, 'geoStructName', 'Model Name')
			writeBox = makeWriteInfoBox(col)
			writeBoxExportType(writeBox, context.scene.geoExportHeaderType, 
				context.scene.geoName, context.scene.geoLevelName,
				context.scene.geoLevelOption)
		
		extendedRAMLabel(col)
		
		#col.prop(context.scene, 'saveCameraSettings')
		#if context.scene.saveCameraSettings:
		#	prop_split(col, context.scene, 'levelCamera', 'Level Camera')
		
		for i in range(panelSeparatorSize):
			col.separator()
		
class SM64_ArmatureToolsPanel(bpy.types.Panel):
	bl_idname = "SM64_PT_armature_tools"
	bl_label = "SM64 Armature Tools"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		col.operator(ArmatureApplyWithMesh.bl_idname)
		col.operator(AddBoneGroups.bl_idname)
		#col.operator(N64_AddF3dMat.bl_idname)

		for i in range(panelSeparatorSize):
			col.separator()

class SM64_ImportDL(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.sm64_import_dl'
	bl_label = "Import Display List"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		romfileSrc = None
		try:
			if context.mode != 'OBJECT':
				raise PluginError("Operator can only be used in object mode.")
		except Exception as e:
			raisePluginError(self, e)
			return {'CANCELLED'}
		try:
			checkExpanded(bpy.path.abspath(context.scene.importRom))
			romfileSrc = open(bpy.path.abspath(context.scene.importRom), 'rb')
			levelParsed = parseLevelAtPointer(romfileSrc, 
				level_pointers[context.scene.levelDLImport])
			segmentData = levelParsed.segmentData
			start = decodeSegmentedAddr(
				int(context.scene.DLImportStart, 16).to_bytes(4, 'big'),
				segmentData) if context.scene.isSegmentedAddrDLImport else \
				int(context.scene.DLImportStart, 16)
			readObj = F3DtoBlenderObject(romfileSrc, start, 
				context.scene, 'sm64_mesh', 
				Matrix.Identity(4),
				segmentData, True)
			
			applyRotation([readObj], math.radians(-90), 'X')
			romfileSrc.close()

			self.report({'INFO'}, 'Generic import succeeded.')
			return {'FINISHED'} # must return a set

		except Exception as e:
			if context.mode != 'OBJECT':
				bpy.ops.object.mode_set(mode = 'OBJECT')
			if romfileSrc is not None:
				romfileSrc.close()
			raisePluginError(self, e)
			return {'CANCELLED'}

class SM64_ImportDLPanel(bpy.types.Panel):
	bl_idname = "SM64_PT_import_dl"
	bl_label = "SM64 DL Importer"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsDLI = col.operator(SM64_ImportDL.bl_idname)

		prop_split(col, context.scene, 'DLImportStart', 'Start Address')
		col.prop(context.scene, 'levelDLImport')
		col.prop(context.scene, 'isSegmentedAddrDLImport')
		col.box().label(text = "Only Fast3D mesh importing allowed.")

		for i in range(panelSeparatorSize):
			col.separator()

class SM64_ExportDL(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.sm64_export_dl'
	bl_label = "Export Display List"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		romfileOutput = None
		tempROM = None
		try:
			if context.mode != 'OBJECT':
				raise PluginError("Operator can only be used in object mode.")	
			allObjs = context.selected_objects
			if len(allObjs) == 0:
				raise PluginError("No objects selected.")
			obj = context.selected_objects[0]
			if not isinstance(obj.data, bpy.types.Mesh):
				raise PluginError("Object is not a mesh.")

			#T, R, S = obj.matrix_world.decompose()
			#objTransform = R.to_matrix().to_4x4() @ \
			#	mathutils.Matrix.Diagonal(S).to_4x4()

			#finalTransform = (blenderToSM64Rotation * \
			#	(bpy.context.scene.blenderToN64Scale)).to_4x4()
			#finalTransform = mathutils.Matrix.Identity(4)
			scaleValue = bpy.context.scene.blenderToN64Scale
			finalTransform = mathutils.Matrix.Diagonal(mathutils.Vector((
				scaleValue, scaleValue, scaleValue))).to_4x4()

			#cProfile.runctx('exportF3DtoC(bpy.path.abspath(context.scene.DLExportPath), obj,' +\
			#	'context.scene.DLExportisStatic, finalTransform,' +\
			#	'context.scene.f3d_type, context.scene.isHWv1,' +\
			#	'bpy.context.scene.DLTexDir,' +\
			#	'bpy.context.scene.DLSaveTextures,' +\
			#	'bpy.context.scene.DLSeparateTextureDef, bpy.context.scene.DLName)',
			#	globals(), locals(), "E:/Non-Steam Games/emulators/Project 64 1.6/SM64 Romhack Tools/_Data/blender.prof")
			#p = pstats.Stats("E:/Non-Steam Games/emulators/Project 64 1.6/SM64 Romhack Tools/_Data/blender.prof")
			#p.sort_stats("cumulative").print_stats(2000)
		except Exception as e:
			raisePluginError(self, e)
			return {"CANCELLED"}
		
		try:
			applyRotation([obj], math.radians(90), 'X')
			exportPath, levelName = getPathAndLevel(context.scene.DLCustomExport, 
				context.scene.DLExportPath, context.scene.DLLevelName, 
				context.scene.DLLevelOption)
			if not context.scene.DLCustomExport:
				applyBasicTweaks(exportPath)
			exportF3DtoC(exportPath, obj,
				"Static" if context.scene.DLExportisStatic else "Dynamic", finalTransform,
				context.scene.f3d_type, context.scene.isHWv1,
				bpy.context.scene.DLTexDir,
				bpy.context.scene.DLSaveTextures or bpy.context.scene.ignoreTextureRestrictions,
				bpy.context.scene.DLSeparateTextureDef,
				bpy.context.scene.DLincludeChildren, bpy.context.scene.DLName, levelName, context.scene.DLGroupName,
				context.scene.DLCustomExport,
				context.scene.DLExportHeaderType)
			self.report({'INFO'}, 'Success!')

			applyRotation([obj], math.radians(-90), 'X')
			return {'FINISHED'} # must return a set

		except Exception as e:
			if context.mode != 'OBJECT':
				bpy.ops.object.mode_set(mode = 'OBJECT')
			applyRotation([obj], math.radians(-90), 'X')
			raisePluginError(self, e)
			return {'CANCELLED'} # must return a set

class Fork_ExportDLPanel(bpy.types.Panel):
	bl_idname = "FAST64_FORK_PT_export_dl"
	bl_label = "Displaylist Exporter"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsDLE = col.operator(SM64_ExportDL.bl_idname)

		col.prop(context.scene, 'DLExportisStatic')
		
		
		col.prop(context.scene, 'DLCustomExport')
		if context.scene.DLCustomExport:
			col.prop(context.scene, 'DLExportPath')
			prop_split(col, context.scene, 'DLName', 'Name')
			if not bpy.context.scene.ignoreTextureRestrictions:
				col.prop(context.scene, 'DLSaveTextures')
				if context.scene.DLSaveTextures:
					prop_split(col, context.scene, 'DLTexDir',
						'Texture Include Path')	
					col.prop(context.scene, 'DLSeparateTextureDef')
			customExportWarning(col)
			
		col.prop(context.scene, 'DLincludeChildren')
		
		for i in range(panelSeparatorSize):
			col.separator()

class SM64_ExportMario(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.sm64_export'
	bl_label = "Export Character"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	def execute(self, context):
		self.report({'ERROR'}, 'Not Implemented.')
		return {'CANCELLED'} # must return a set

class SM64_ExportCharacterPanel(bpy.types.Panel):
	bl_idname = "SM64_PT_export_character"
	bl_label = "SM64 Character Exporter"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsE = col.operator(SM64_ExportMario.bl_idname)
	
		for i in range(panelSeparatorSize):
			col.separator()

class SM64_ImportMario(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.sm64_import'
	bl_label = "Import Character"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		characterImportData = sm64_character_data[context.scene.sm64_character]
			
		self.report({'ERROR'}, 'Not Implemented.')
		return {'CANCELLED'} # must return a set

class SM64_ImportCharacterPanel(bpy.types.Panel):
	bl_idname = "SM64_PT_import_character"
	bl_label = "SM64 Character Importer"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		col.prop(context.scene, 'sm64_character')
		col.prop(context.scene, 'characterIgnoreSwitch')
		propsI = col.operator(SM64_ImportMario.bl_idname)

		for i in range(panelSeparatorSize):
			col.separator()

class SM64_ImportLevel(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.sm64_import_lvl'
	bl_label = "Import Level"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		self.report({'ERROR'}, "Not Implemented.")
		return {'CANCELLED'} # must return a set

class SM64_ImportLevelPanel(bpy.types.Panel):
	bl_idname = "SM64_PT_import_level"
	bl_label = "SM64 Level Importer"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsLI = col.operator(SM64_ImportLevel.bl_idname)
		col.prop(context.scene, 'levelLevel')

		for i in range(panelSeparatorSize):
			col.separator()

class SM64_ExportLevel(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.sm64_export_level'
	bl_label = "Export Level"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	def execute(self, context):
		
		try:
			if context.mode != 'OBJECT':
				raise PluginError("Operator can only be used in object mode.")
			if len(context.selected_objects) == 0:
				raise PluginError("Object not selected.")
			obj = context.selected_objects[0]
			if obj.data is not None or obj.sm64_obj_type != 'Level Root':
				raise PluginError("The selected object is not an empty with the Level Root type.")

			#obj = context.active_object

			scaleValue = bpy.context.scene.blenderToN64Scale
			finalTransform = mathutils.Matrix.Diagonal(mathutils.Vector((
				scaleValue, scaleValue, scaleValue))).to_4x4()
		
		except Exception as e:
			raisePluginError(self, e)
			return {'CANCELLED'} # must return a set
		try:
			applyRotation([obj], math.radians(90), 'X')
			if context.scene.levelCustomExport:
				exportPath = bpy.path.abspath(context.scene.levelExportPath)
				levelName = context.scene.levelName
				triggerName = 'sCam' + context.scene.levelName.title().replace(' ', '').replace('_', '')
			else:
				exportPath = bpy.path.abspath(context.scene.decompPath)
				if context.scene.levelOption == 'custom':
					levelName = context.scene.levelName
					triggerName = 'sCam' + context.scene.levelName.title().replace(' ', '').replace('_', '')
				else:
					levelName = context.scene.levelOption
					triggerName = cameraTriggerNames[context.scene.levelOption]
			if not context.scene.levelCustomExport:
				applyBasicTweaks(exportPath)
			#cProfile.runctx('exportLevelC(obj, finalTransform,' +\
			#	'context.scene.f3d_type, context.scene.isHWv1, levelName, exportPath,' +\
			#	'context.scene.levelSaveTextures or bpy.context.scene.ignoreTextureRestrictions,' +\
			#	'context.scene.levelCustomExport, triggerName, "Static")',
			#	globals(), locals(), "E:/blender.prof")
			#p = pstats.Stats("E:/blender.prof")
			#p.sort_stats("cumulative").print_stats(2000)
			exportLevelC(obj, finalTransform,
				context.scene.f3d_type, context.scene.isHWv1, levelName, exportPath, 
				context.scene.levelSaveTextures or bpy.context.scene.ignoreTextureRestrictions, 
				context.scene.levelCustomExport, triggerName, "Static")
			self.report({'INFO'}, 'Success!')

			applyRotation([obj], math.radians(-90), 'X')
			#applyRotation(obj.children, math.radians(0), 'X')
			return {'FINISHED'} # must return a set

		except Exception as e:
			if context.mode != 'OBJECT':
				bpy.ops.object.mode_set(mode = 'OBJECT')

			applyRotation([obj], math.radians(-90), 'X')
			#applyRotation(obj.children, math.radians(0), 'X')

			obj.select_set(True)
			context.view_layer.objects.active = obj
			raisePluginError(self, e)
			return {'CANCELLED'} # must return a set

class Fork_ExportLevelPanel(bpy.types.Panel):
	bl_idname = "FAST64_FORK_PT_export_level"
	bl_label = "Level Exporter"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		col.label(text = 'This is for decomp only.')
		col.operator(SM64_ExportLevel.bl_idname)
		if not bpy.context.scene.ignoreTextureRestrictions:
			col.prop(context.scene, 'levelSaveTextures')
		col.prop(context.scene, 'levelCustomExport')
		if context.scene.levelCustomExport:
			prop_split(col, context.scene, 'levelExportPath', 'Directory')
			prop_split(col, context.scene, 'levelName', 'Name')
			customExportWarning(col)
		else:
			col.prop(context.scene, 'levelOption')
			if context.scene.levelOption == 'custom':
				levelName = context.scene.levelName
				box = col.box()
				box.label(text = 'Adding levels may require modifying the save file format.')
				box.label(text = 'Check src/game/save_file.c.')
				prop_split(col, context.scene, 'levelName', 'Name')
			else:
				levelName = context.scene.levelOption
			# decompFolderMessage(col)
			writeBox = makeWriteInfoBox(col)
			writeBox.label(text = 'levels/' + toAlnum(levelName) + ' (data).')
			writeBox.label(text = 'src/game/camera.c (camera volume).')
			writeBox.label(text = 'levels/level_defines.h (camera volume).')
		
		extendedRAMLabel(col)
		#prop_split(col, context.scene, 'levelCamera', 'Camera')
		for i in range(panelSeparatorSize):
			col.separator()

def extendedRAMLabel(layout):
	return
	infoBox = layout.box()
	infoBox.label(text = 'Be sure to add: ')
	infoBox.label(text = '"#define USE_EXT_RAM"')
	infoBox.label(text = 'to include/segments.h.')
	infoBox.label(text = 'Extended RAM prevents crashes.')

class SM64_ImportAnimMario(bpy.types.Operator):
	bl_idname = 'object.sm64_import_anim'
	bl_label = "Import Animation"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		romfileSrc = None
		try:
			checkExpanded(bpy.path.abspath(context.scene.importRom))
			romfileSrc = open(bpy.path.abspath(context.scene.importRom), 'rb')
		except Exception as e:
			raisePluginError(self, e)
			return {'CANCELLED'}
		try:
			levelParsed = parseLevelAtPointer(romfileSrc, 
				level_pointers[context.scene.levelAnimImport])
			segmentData = levelParsed.segmentData

			animStart = int(context.scene.animStartImport, 16)
			if context.scene.animIsSegPtr:
				animStart = decodeSegmentedAddr(
					animStart.to_bytes(4, 'big'), segmentData)

			if not context.scene.isDMAImport and context.scene.animIsAnimList:
				romfileSrc.seek(animStart + 4 * context.scene.animListIndexImport)
				actualPtr = romfileSrc.read(4)
				animStart = decodeSegmentedAddr(actualPtr, segmentData)

			if len(context.selected_objects) == 0:
				raise PluginError("Armature not selected.")
			armatureObj = context.active_object
			if type(armatureObj.data) is not bpy.types.Armature:
				raise PluginError("Armature not selected.")
			
			importAnimationToBlender(romfileSrc, 
				animStart, armatureObj, 
				segmentData, context.scene.isDMAImport)
			romfileSrc.close()
			self.report({'INFO'}, 'Success!')
		except Exception as e:
			if romfileSrc is not None:
				romfileSrc.close()
			raisePluginError(self, e)
			return {'CANCELLED'} # must return a set

		return {'FINISHED'} # must return a set

class SM64_ImportAnimPanel(bpy.types.Panel):
	bl_idname = "SM64_PT_import_anim"
	bl_label = "SM64 Animation Importer"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsAnimImport = col.operator(SM64_ImportAnimMario.bl_idname)
		col.prop(context.scene, 'isDMAImport')
		if not context.scene.isDMAImport:
			col.prop(context.scene, 'animIsAnimList')
			if context.scene.animIsAnimList:
				prop_split(col, context.scene, 'animListIndexImport', 
					'Anim List Index')

		prop_split(col, context.scene, 'animStartImport', 'Start Address')
		col.prop(context.scene, 'animIsSegPtr')
		col.prop(context.scene, 'levelAnimImport')

		for i in range(panelSeparatorSize):
			col.separator()
		
class Fork_ExportAnim(bpy.types.Operator):
	bl_idname = 'object.sm64_export_anim'
	bl_label = "Export Animation"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		romfileOutput = None
		tempROM = None
		try:
			if context.mode != 'OBJECT':
				raise PluginError("Operator can only be used in object mode.")
			if len(context.selected_objects) == 0 or not \
				isinstance(context.selected_objects[0].data, bpy.types.Armature):
				raise PluginError("Armature not selected.")
			if len(context.selected_objects) > 1 :
				raise PluginError("Multiple objects selected, make sure to select only one.")
			armatureObj = context.selected_objects[0]
		except Exception as e:
			raisePluginError(self, e)
			return {"CANCELLED"}

		try:
			exportPath, levelName = getPathAndLevel(context.scene.animCustomExport, 
				context.scene.animExportPath, context.scene.animLevelName, 
				context.scene.animLevelOption)
			if not context.scene.animCustomExport:
				applyBasicTweaks(exportPath)
			exportAnimationC(armatureObj, context.scene.loopAnimation, 
				exportPath, bpy.context.scene.animName,
				context.scene.animCustomExport, context.scene.animExportHeaderType, levelName)
			self.report({'INFO'}, 'Success!')
		except Exception as e:
			raisePluginError(self, e)
			return {'CANCELLED'} # must return a set

		return {'FINISHED'} # must return a set

class Fork_ExportAnimPanel(bpy.types.Panel):
	bl_idname = "FAST64_FORK_PT_export_anim"
	bl_label = "Animation Exporter"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsAnimExport = col.operator(Fork_ExportAnim.bl_idname)
		
		col.prop(context.scene, 'loopAnimation')
		col.prop(context.scene, 'animCustomExport')
		if context.scene.animCustomExport:
			col.prop(context.scene, 'animExportPath')
			prop_split(col, context.scene, 'animName', 'Name')
			customExportWarning(col)
		else:
			prop_split(col, context.scene, 'animExportHeaderType', 'Export Type')
			prop_split(col, context.scene, 'animName', 'Name')
			if context.scene.animExportHeaderType == 'Level':
				prop_split(col, context.scene, 'animLevelOption', 'Level')
				if context.scene.animLevelOption == 'custom':
					prop_split(col, context.scene, 'animLevelName', 'Level Name')
			
			# decompFolderMessage(col)
			writeBox = makeWriteInfoBox(col)
			writeBoxExportType(writeBox, context.scene.animExportHeaderType, 
				context.scene.animName, context.scene.animLevelName,
				context.scene.animLevelOption)

			col.separator()
			

		for i in range(panelSeparatorSize):
			col.separator()

class Fork_ExportCollision(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.sm64_export_collision'
	bl_label = "Export Collision"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	def execute(self, context):
		romfileOutput = None
		tempROM = None
		try:
			obj = None
			if context.mode != 'OBJECT':
				raise PluginError("Operator can only be used in object mode.")
			if len(context.selected_objects) == 0:
				raise PluginError("Object not selected.")
			obj = context.active_object
			#if type(obj.data) is not bpy.types.Mesh:
			#	raise PluginError("Mesh not selected.")
		
			#T, R, S = obj.matrix_world.decompose()
			#objTransform = R.to_matrix().to_4x4() @ \
			#	mathutils.Matrix.Diagonal(S).to_4x4()
			#finalTransform = (blenderToSM64Rotation * \
			#	(bpy.context.scene.blenderToN64Scale)).to_4x4()
			#finalTransform = mathutils.Matrix.Identity(4)

			scaleValue = bpy.context.scene.blenderToN64Scale
			finalTransform = mathutils.Matrix.Diagonal(mathutils.Vector((
				scaleValue, scaleValue, scaleValue))).to_4x4()
		except Exception as e:
			raisePluginError(self, e)
			return {"CANCELLED"}
		
		try:
			applyRotation([obj], math.radians(-90), 'X')
			
			exportPath, levelName = getPathAndLevel(context.scene.colCustomExport, 
				context.scene.colExportPath, context.scene.colLevelName, 
				context.scene.colLevelOption)
			if not context.scene.colCustomExport:
				applyBasicTweaks(exportPath)
			exportCollisionC(obj, finalTransform,
				exportPath, False,
				context.scene.colIncludeChildren, 
				bpy.context.scene.colName, context.scene.colCustomExport, context.scene.colExportRooms,
				context.scene.colExportHeaderType, levelName)
			self.report({'INFO'}, 'Success!')

			applyRotation([obj], math.radians(90), 'X')
			return {'FINISHED'} # must return a set

		except Exception as e:
			if context.mode != 'OBJECT':
				bpy.ops.object.mode_set(mode = 'OBJECT')

			applyRotation([obj], math.radians(90), 'X')

			obj.select_set(True)
			context.view_layer.objects.active = obj
			raisePluginError(self, e)
			return {'CANCELLED'} # must return a set

class Fork_ExportCollisionPanel(bpy.types.Panel):
	bl_idname = "FORK_PT_export_collision"
	bl_label = "Collision Exporter"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsColE = col.operator(Fork_ExportCollision.bl_idname)

		col.prop(context.scene, 'colIncludeChildren')
		
		col.prop(context.scene, 'colExportRooms')
		col.prop(context.scene, 'colCustomExport')
		if context.scene.colCustomExport:
			col.prop(context.scene, 'colExportPath')
			prop_split(col, context.scene, 'colName', 'Name')
			customExportWarning(col)
		else:
			prop_split(col, context.scene, 'colExportHeaderType', 'Export Type')
			prop_split(col, context.scene, 'colName', 'Name')
			# if context.scene.colExportHeaderType == 'Actor':
				# prop_split(col, context.scene, 'colGroupName', 'Group Name')
			if context.scene.colExportHeaderType == 'Level':
				prop_split(col, context.scene, 'colLevelOption', 'Level')
				if context.scene.colLevelOption == 'custom':
					prop_split(col, context.scene, 'colLevelName', 'Level Name')
			
			# decompFolderMessage(col)
			writeBox = makeWriteInfoBox(col)
			writeBoxExportType(writeBox, context.scene.colExportHeaderType, 
				context.scene.colName, context.scene.colLevelName, context.scene.colLevelOption)
			
		for i in range(panelSeparatorSize):
			col.separator()

class ExportTexRectDraw(bpy.types.Operator):
	# set bl_ properties
	bl_idname = 'object.f3d_texrect_draw'
	bl_label = "Export F3D Texture Rectangle"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		try:
			if context.scene.texrect.tex is None:
				raise PluginError("No texture selected.")
			else:
				if context.scene.decompPath == "":
					raise PluginError("Decomp path has not been set in File Settings.")

				if context.scene.TexRectCustomExport:
					exportPath = context.scene.TexRectExportPath
				else:
					exportPath = context.scene.decompPath
				if not context.scene.TexRectCustomExport:
					applyBasicTweaks(exportPath)
				exportTexRectToC(bpy.path.abspath(exportPath), 
					context.scene.texrect,
					context.scene.f3d_type, context.scene.isHWv1,
					'textures/segment2',
					context.scene.TexRectSaveTextures or bpy.context.scene.ignoreTextureRestrictions,
					context.scene.TexRectName,
					not context.scene.TexRectCustomExport,
					enumHUDPaths[context.scene.TexRectExportType])

				self.report({'INFO'}, 'Success!')
		except Exception as e:
			raisePluginError(self, e)
			return {"CANCELLED"}
		return {'FINISHED'} # must return a set

class UnlinkTexRect(bpy.types.Operator):
	bl_idname = 'image.texrect_unlink'
	bl_label = "Unlink TexRect Image"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	# Called on demand (i.e. button press, menu item)
	# Can also be called from operator search menu (Spacebar)
	def execute(self, context):
		context.scene.texrect.tex = None
		return {'FINISHED'} # must return a set

class ExportTexRectDrawPanel(bpy.types.Panel):
	bl_idname = "export_texrect"
	bl_label = "Texrect Exporter"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		propsTexRectE = col.operator(ExportTexRectDraw.bl_idname)

		textureProp = context.scene.texrect
		tex = textureProp.tex
		col.label(text = 'This is for decomp only.')
		col.template_ID(textureProp, 'tex', new="image.new", open="image.open", unlink="image.texrect_unlink")
		#col.prop(textureProp, 'tex')

		tmemUsageUI(col, textureProp)
		if tex is not None and tex.size[0] > 0 and tex.size[1] > 0:
			col.prop(textureProp, 'tex_format', text = 'Format')
			if textureProp.tex_format[:2] == 'CI':
				col.prop(textureProp, 'ci_format', text = 'CI Format')
			col.prop(textureProp.S, 'clamp', text = 'Clamp S')
			col.prop(textureProp.T, 'clamp', text = 'Clamp T')
			col.prop(textureProp.S, 'mirror', text = 'Mirror S')
			col.prop(textureProp.T, 'mirror', text = 'Mirror T')
			
		prop_split(col, context.scene, 'TexRectName', 'Name')
		if not bpy.context.scene.ignoreTextureRestrictions:
			col.prop(context.scene, 'TexRectSaveTextures')
		col.prop(context.scene, 'TexRectCustomExport')
		if context.scene.TexRectCustomExport:
			col.prop(context.scene, 'TexRectExportPath')
			customExportWarning(col)
		else:
			prop_split(col, context.scene, 'TexRectExportType', 'Export Type')
			if not context.scene.TexRectCustomExport:
				# decompFolderMessage(col)
				writeBox = makeWriteInfoBox(col)
				writeBox.label(text = 'bin/segment2.c')
				writeBox.label(text = 'src/game/segment2.h')
				writeBox.label(text = 'textures/segment2')
			infoBox = col.box()
			infoBox.label(text = 'After export, call your hud\'s draw function in ')
			infoBox.label(text = enumHUDPaths[context.scene.TexRectExportType][0] + ': ')
			infoBox.label(text = enumHUDPaths[context.scene.TexRectExportType][1] + '.')

		for i in range(panelSeparatorSize):
			col.separator()

class F3D_GlobalSettingsPanel(bpy.types.Panel):
	bl_idname = "F3D_PT_global_settings"
	bl_label = "F3D Global Settings"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		col.prop(context.scene, 'f3d_type')
		col.prop(context.scene, 'isHWv1')
		
class Fork_FileSettingsPanel(bpy.types.Panel):
	bl_idname = "FAST64_FORK_PT_file_settings"
	bl_label = "File Settings"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()	
		prop_split(col, context.scene, 'blenderToN64Scale', 'Blender To N64 Scale')
		col.prop(context.scene, 'fullTraceback')
		
		col.prop(context.scene, 'disableScroll')
		col.prop(context.scene, 'ignoreTextureRestrictions')
		if context.scene.ignoreTextureRestrictions:
			col.box().label(text = "Width/height must be < 1024. Must be RGBA32. Must be png format.")
		col.prop(context.scene, 'decompPath')

class SM64_AddressConvertPanel(bpy.types.Panel):
	bl_idname = "SM64_PT_addr_conv"
	bl_label = "SM64 Address Converter"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Fast64 Fork'

	@classmethod
	def poll(cls, context):
		return True

	# called every frame
	def draw(self, context):
		col = self.layout.column()
		segToVirtOp = col.operator(SM64_AddrConv.bl_idname, 
			text = "Convert Segmented To Virtual")
		segToVirtOp.segToVirt = True
		virtToSegOp = col.operator(SM64_AddrConv.bl_idname, 
			text = "Convert Virtual To Segmented")
		virtToSegOp.segToVirt = False
		prop_split(col, context.scene, 'convertibleAddr', 'Address')
		col.prop(context.scene, 'levelConvert')

classes = (
	ArmatureApplyWithMesh,
	AddBoneGroups,
	N64_AddF3dMat,

	F3D_GlobalSettingsPanel,
	Fork_FileSettingsPanel,
	#SM64_AddressConvertPanel,
	#SM64_ImportCharacterPanel,
	#SM64_ExportCharacterPanel,
	#SM64_ImportGeolayoutPanel,
	Fork_ModelExportPanel,
	#SM64_ArmatureToolsPanel,
	#SM64_ImportAnimPanel,
	Fork_ExportAnimPanel,
	#SM64_ImportDLPanel,
	Fork_ExportDLPanel,
	#SM64_ImportLevelPanel,
	Fork_ExportLevelPanel,
	Fork_ExportCollisionPanel,
	ExportTexRectDrawPanel,
	UnlinkTexRect,

	#SM64_ImportMario,
	#SM64_ExportMario,
	#SM64_ImportGeolayout,
	Fork_ExportModelFromArmature,
	Fork_ExportModelFromMesh,
	#SM64_ImportDL,
	SM64_ExportDL,
	#SM64_ImportAnimMario,
	Fork_ExportAnim,
	#SM64_ImportLevel
	SM64_ExportLevel,
	Fork_ExportCollision,
	ExportTexRectDraw,
)

# called on add-on enabling
# register operators and panels here
# append menu layout drawing function to an existing window
def register():
	col_register() # register first, so panel goes above mat panel
	mat_register()
	bone_register()
	cam_register()
	sm64_obj_register()
	level_register()
	render_engine_register()
	bsdf_conv_register()
	sm64_spline_register()

	for cls in classes:
		register_class(cls)

	# Camera
	#bpy.types.Scene.saveCameraSettings = bpy.props.BoolProperty(
	#	name = 'Save Level Camera Settings', default = False)
	#bpy.types.Scene.levelCamera = bpy.props.PointerProperty(
	#	type = bpy.types.Camera, name = 'Level Camera')

	# Character
	bpy.types.Scene.rotationAxis = bpy.props.FloatVectorProperty(
		size = 3, default = (1,0,0))
	bpy.types.Scene.rotationAngle = bpy.props.FloatProperty(default = 90)
	bpy.types.Scene.rotationOrder = bpy.props.StringProperty(default = 'XYZ')

	bpy.types.Scene.sm64_character = bpy.props.EnumProperty(
		items = character_enums, name = 'SM64 Character', default = 'Mario')
	bpy.types.Scene.useFaceAnimation = bpy.props.BoolProperty(
		name ='Use Face Animation?')
	bpy.types.Scene.overwriteWingPositions = bpy.props.BoolProperty(
		name ='Overwrite Wing Positions? (See attatched diagram)')
	bpy.types.Scene.exportRange = bpy.props.IntVectorProperty(name="Export range",
		default=marioFullRomInterval, size = 2, min = 0)
	bpy.types.Scene.segment4 = bpy.props.IntVectorProperty(name="Segment 4", 
		default=defaultExtendSegment4, size = 2, min = 0)
	bpy.types.Scene.useCustomSegment4 = bpy.props.BoolProperty(
		name = "Use custom segment 4?", default = True)
	bpy.types.Scene.useLogFile = bpy.props.BoolProperty(name ='Write log file?')
	bpy.types.Scene.logFilePath = bpy.props.StringProperty(
		name = 'Log File', subtype = 'FILE_PATH')

	# Display List
	bpy.types.Scene.DLImportStart = bpy.props.StringProperty(
		name ='Start Address', default = 'A3BE1C')
	bpy.types.Scene.DLExportStart = bpy.props.StringProperty(
		name = 'Start', default = '11D8930')
	bpy.types.Scene.DLExportEnd = bpy.props.StringProperty(
		name = 'End', default = '11FFF00')
	bpy.types.Scene.levelDLImport = bpy.props.EnumProperty(items = level_enums, 
		name = 'Level', default = 'CG')
	bpy.types.Scene.levelDLExport = bpy.props.EnumProperty(items = level_enums, 
		name = 'Level', default = 'WF')
	bpy.types.Scene.DLExportGeoPtr = bpy.props.StringProperty(
		name ='Geolayout Pointer', default = '132AA8')
	bpy.types.Scene.overwriteGeoPtr = bpy.props.BoolProperty(
		name = "Overwrite geolayout pointer", default = False)
	bpy.types.Scene.isSegmentedAddrDLImport = bpy.props.BoolProperty(
		name = 'Is Segmented Address', default = False)
	bpy.types.Scene.DLExportPath = bpy.props.StringProperty(
		name = 'Directory', subtype = 'FILE_PATH')
	bpy.types.Scene.DLExportisStatic = bpy.props.BoolProperty(
		name = 'Static DL', default = True)
	bpy.types.Scene.DLDefinePath = bpy.props.StringProperty(
		name = 'Definitions Filepath', subtype = 'FILE_PATH')
	bpy.types.Scene.DLUseBank0 = bpy.props.BoolProperty(name = 'Use Bank 0')
	bpy.types.Scene.DLRAMAddr = bpy.props.StringProperty(name = 'RAM Address', 
		default = '80000000')
	bpy.types.Scene.DLTexDir = bpy.props.StringProperty(
		name ='Include Path', default = 'levels/bob')
	bpy.types.Scene.DLSaveTextures = bpy.props.BoolProperty(
		name = 'Save Textures As PNGs (Breaks CI Textures)')
	bpy.types.Scene.DLSeparateTextureDef = bpy.props.BoolProperty(
		name = 'Save texture.inc.c separately')
	
	bpy.types.Scene.DLincludeChildren = bpy.props.BoolProperty(
		name = 'Include Children')
	bpy.types.Scene.DLInsertableBinaryPath = bpy.props.StringProperty(
		name = 'Filepath', subtype = 'FILE_PATH')
	bpy.types.Scene.DLName = bpy.props.StringProperty(
		name = 'Name', default = 'mario')
	bpy.types.Scene.DLCustomExport = bpy.props.BoolProperty(
		name = 'Custom Export Path')
	bpy.types.Scene.DLExportHeaderType = bpy.props.EnumProperty(
		items = enumExportHeaderType, name = 'Header Export', default = 'Actor')
	bpy.types.Scene.DLGroupName = bpy.props.StringProperty(name = 'Group Name', 
		default = 'group0')
	bpy.types.Scene.DLLevelName = bpy.props.StringProperty(name = 'Level', 
		default = 'bob')
	bpy.types.Scene.DLLevelOption = bpy.props.EnumProperty(
		items = enumLevelNames, name = 'Level', default = 'bob')
	
	# Geolayouts
	bpy.types.Scene.levelGeoImport = bpy.props.EnumProperty(items = level_enums,
		name = 'Level', default = 'HMC')
	bpy.types.Scene.levelGeoExport = bpy.props.EnumProperty(items = level_enums,
		name = 'Level', default = 'HMC')
	bpy.types.Scene.geoExportStart = bpy.props.StringProperty(
		name = 'Start', default = '11D8930')
	bpy.types.Scene.geoExportEnd = bpy.props.StringProperty(
		name = 'End', default = '11FFF00')
	bpy.types.Scene.generateArmature = bpy.props.BoolProperty(
		name ='Generate Armature?', default = True)
	bpy.types.Scene.geoImportAddr = bpy.props.StringProperty(
		name ='Start Address', default = '1F1D60')
	bpy.types.Scene.overwriteModelLoad = bpy.props.BoolProperty(
		name = 'Modify level script', default = True)
	bpy.types.Scene.modelLoadLevelScriptCmd = bpy.props.StringProperty(
		name = 'Level script model load command', default = '2ABCE0')
	bpy.types.Scene.modelID = bpy.props.StringProperty(name = 'Model ID', 
		default = '1')
	bpy.types.Scene.ignoreSwitch = bpy.props.BoolProperty(
		name = 'Ignore Switch Nodes', default = True)
	bpy.types.Scene.textDumpGeo = bpy.props.BoolProperty(
		name = 'Dump geolayout as text', default = False)
	bpy.types.Scene.textDumpGeoPath =  bpy.props.StringProperty(
		name ='Text Dump Path', subtype = 'FILE_PATH')
	bpy.types.Scene.geoExportPath = bpy.props.StringProperty(
		name = 'Directory', subtype = 'FILE_PATH')
	bpy.types.Scene.geoUseBank0 = bpy.props.BoolProperty(name = 'Use Bank 0')
	bpy.types.Scene.geoRAMAddr = bpy.props.StringProperty(name = 'RAM Address', 
		default = '80000000')
	bpy.types.Scene.geoTexDir = bpy.props.StringProperty(
		name ='Include Path', default = 'assets/mesh/')
	bpy.types.Scene.geoSaveTextures = bpy.props.BoolProperty(
		name = 'Save Textures As PNGs (Breaks CI Textures)')
	bpy.types.Scene.geoSeparateTextureDef = bpy.props.BoolProperty(
		name = 'Save texture.inc.c separately')
	bpy.types.Scene.geoInsertableBinaryPath = bpy.props.StringProperty(
		name = 'Filepath', subtype = 'FILE_PATH')
	bpy.types.Scene.geoIsSegPtr = bpy.props.BoolProperty(
		name = 'Is Segmented Address')
	bpy.types.Scene.geoName = bpy.props.StringProperty(
		name = 'Directory Name', default = 'mesh')
	bpy.types.Scene.geoGroupName = bpy.props.StringProperty(
		name = 'Name', default = 'group0')
	bpy.types.Scene.geoExportHeaderType = bpy.props.EnumProperty(
		name = 'Header Export', items = enumExportHeaderType, default = 'Actor')
	bpy.types.Scene.geoCustomExport = bpy.props.BoolProperty(
		name = 'Custom Export Path')
	bpy.types.Scene.geoLevelName = bpy.props.StringProperty(name = 'Level', 
		default = 'bob')
	bpy.types.Scene.geoLevelOption = bpy.props.EnumProperty(
		items = enumLevelNames, name = 'Level', default = 'bob')
	bpy.types.Scene.modifyOldGeo = bpy.props.BoolProperty(
		name = 'Rename old geolayout to avoid conflicts', default = True)
	bpy.types.Scene.geoStructName = bpy.props.StringProperty(name = 'Geolayout Name',
		default = 'mesh_model')

	# Level
	bpy.types.Scene.levelLevel = bpy.props.EnumProperty(items = level_enums, 
		name = 'Level', default = 'CG')

	# Animation
	bpy.types.Scene.animStartImport = bpy.props.StringProperty(
		name ='Import Start', default = '4EC690')
	bpy.types.Scene.isDMAImport = bpy.props.BoolProperty(name = 'Is DMA Animation', default = True)
	bpy.types.Scene.isDMAExport = bpy.props.BoolProperty(name = 'Is DMA Animation')
	bpy.types.Scene.DMAEntryAddress = bpy.props.StringProperty(name = 'DMA Entry Address', default = '4EC008')
	bpy.types.Scene.DMAStartAddress = bpy.props.StringProperty(name = 'DMA Start Address', default = '4EC000')
	bpy.types.Scene.levelAnimImport = bpy.props.EnumProperty(items = level_enums, name = 'Level', default = 'IC')
	bpy.types.Scene.levelAnimExport = bpy.props.EnumProperty(items = level_enums, name = 'Level', default = 'IC')
	bpy.types.Scene.loopAnimation = bpy.props.BoolProperty(name = 'Loop Animation', default = True)
	bpy.types.Scene.setAnimListIndex = bpy.props.BoolProperty(name = 'Set Anim List Entry', default = True)
	bpy.types.Scene.overwrite_0x28 = bpy.props.BoolProperty(name = 'Overwrite 0x28 behaviour command', default = True)
	bpy.types.Scene.addr_0x27 = bpy.props.StringProperty(
		name = '0x27 Command Address', default = '21CD00')
	bpy.types.Scene.addr_0x28 = bpy.props.StringProperty(
		name = '0x28 Command Address', default = '21CD08')
	bpy.types.Scene.animExportPath = bpy.props.StringProperty(
		name = 'Directory', subtype = 'FILE_PATH')
	bpy.types.Scene.animOverwriteDMAEntry = bpy.props.BoolProperty(
		name = 'Overwrite DMA Entry')
	bpy.types.Scene.animInsertableBinaryPath = bpy.props.StringProperty(
		name = 'Filepath', subtype = 'FILE_PATH')
	bpy.types.Scene.animIsSegPtr = bpy.props.BoolProperty(
		name = 'Is Segmented Address', default = False)
	bpy.types.Scene.animIsAnimList = bpy.props.BoolProperty(
		name = 'Is Anim List', default = True)
	bpy.types.Scene.animListIndexImport = bpy.props.IntProperty(
		name = 'Anim List Index', min = 0, max = 255)
	bpy.types.Scene.animListIndexExport = bpy.props.IntProperty(
		name = "Anim List Index", min = 0, max = 255)
	bpy.types.Scene.animName = bpy.props.StringProperty(
		name = 'Name', default = 'mesh')
	bpy.types.Scene.animWriteHeaders = bpy.props.BoolProperty(
		name = 'Write Headers For Actor', default = True)
	bpy.types.Scene.animCustomExport = bpy.props.BoolProperty(
		name = 'Custom Export Path')
	bpy.types.Scene.animExportHeaderType = bpy.props.EnumProperty(
		items = enumExportHeaderType, name = 'Header Export', default = 'Actor')
	bpy.types.Scene.animLevelName = bpy.props.StringProperty(name = 'Level', 
		default = 'bob')
	bpy.types.Scene.animLevelOption = bpy.props.EnumProperty(
		items = enumLevelNames, name = 'Level', default = 'bob')

	# Collision
	bpy.types.Scene.colExportPath = bpy.props.StringProperty(
		name = 'Directory', subtype = 'FILE_PATH')
	bpy.types.Scene.colExportLevel = bpy.props.EnumProperty(items = level_enums, 
		name = 'Level Used By Collision', default = 'WF')
	bpy.types.Scene.addr_0x2A = bpy.props.StringProperty(
		name = '0x2A Behaviour Command Address', default = '21A9CC')
	bpy.types.Scene.set_addr_0x2A = bpy.props.BoolProperty(
		name = 'Overwrite 0x2A Behaviour Command')
	bpy.types.Scene.colStartAddr = bpy.props.StringProperty(name ='Start Address',
		default = '11D8930')
	bpy.types.Scene.colEndAddr = bpy.props.StringProperty(name ='Start Address',
		default = '11FFF00')
	bpy.types.Scene.colIncludeChildren = bpy.props.BoolProperty(
		name = 'Include child objects', default = True)
	bpy.types.Scene.colInsertableBinaryPath = bpy.props.StringProperty(
		name = 'Filepath', subtype = 'FILE_PATH')
	bpy.types.Scene.colExportRooms = bpy.props.BoolProperty(
		name = 'Export Rooms', default = False)
	bpy.types.Scene.colName = bpy.props.StringProperty(
		name = 'Name', default = 'mario')
	bpy.types.Scene.colCustomExport = bpy.props.BoolProperty(
		name = 'Custom Export Path')
	bpy.types.Scene.colExportHeaderType = bpy.props.EnumProperty(
		items = enumExportHeaderType, name = 'Header Export', default = 'Actor')
	bpy.types.Scene.colLevelName = bpy.props.StringProperty(name = 'Level', 
		default = 'bob')
	bpy.types.Scene.colLevelOption = bpy.props.EnumProperty(
		items = enumLevelNames, name = 'Level', default = 'bob')

	# Texrect
	bpy.types.Scene.texrect = bpy.props.PointerProperty(type = TextureProperty)
	bpy.types.Scene.texrectImageTexture = bpy.props.PointerProperty(type = bpy.types.ImageTexture)
	bpy.types.Scene.TexRectExportPath = bpy.props.StringProperty(name = 'Export Path', subtype='FILE_PATH')
	bpy.types.Scene.TexRectTexDir = bpy.props.StringProperty(name = 'Include Path', default = 'textures/segment2')
	bpy.types.Scene.TexRectSaveTextures = bpy.props.BoolProperty(name = 'Save Textures as PNGs (Breaks CI Textures)')
	bpy.types.Scene.TexRectName = bpy.props.StringProperty(name = 'Name', default = 'render_hud_image')
	bpy.types.Scene.TexRectCustomExport = bpy.props.BoolProperty(name = 'Custom Export Path')
	bpy.types.Scene.TexRectExportType = bpy.props.EnumProperty(name = 'Export Type', items = enumHUDExportLocation)

	# Objects
	#bpy.types.Scene.levelCamera = bpy.props.PointerProperty(type = bpy.types.Camera)
	bpy.types.Scene.levelName = bpy.props.StringProperty(name = 'Name', default = 'bob')
	bpy.types.Scene.levelOption = bpy.props.EnumProperty(name = "Level", items = enumLevelNames, default = 'bob')
	bpy.types.Scene.levelExportPath = bpy.props.StringProperty(
		name = 'Directory', subtype = 'FILE_PATH')
	bpy.types.Scene.levelSaveTextures = bpy.props.BoolProperty(
		name = 'Save Textures As PNGs (Breaks CI Textures)')
	bpy.types.Scene.levelCustomExport = bpy.props.BoolProperty(
		name = 'Custom Export Path')

	# ROM
	bpy.types.Scene.importRom = bpy.props.StringProperty(
		name ='Import ROM', subtype = 'FILE_PATH')
	bpy.types.Scene.exportRom = bpy.props.StringProperty(
		name ='Export ROM', subtype = 'FILE_PATH')
	bpy.types.Scene.outputRom = bpy.props.StringProperty(
		name ='Output ROM', subtype = 'FILE_PATH')
	bpy.types.Scene.extendBank4 = bpy.props.BoolProperty(
		name = 'Extend Bank 4 on Export?', default = True, 
		description = 'Sets bank 4 range to (' +\
			hex(defaultExtendSegment4[0]) + ', ' + \
			hex(defaultExtendSegment4[1]) + ') and copies data from old bank')
	bpy.types.Scene.convertibleAddr = bpy.props.StringProperty(
		name = 'Address')
	bpy.types.Scene.levelConvert = bpy.props.EnumProperty(
		items = level_enums, name = 'Level', default = 'IC')
	bpy.types.Scene.blenderToN64Scale = bpy.props.FloatProperty(
		name = 'Blender To N64 Scale', default = 100.00)
	bpy.types.Scene.decompPath = bpy.props.StringProperty(
		name ='Game Folder', subtype = 'FILE_PATH')
	bpy.types.Scene.disableScroll = bpy.props.BoolProperty(
		name = 'Disable Scrolling Textures')
	bpy.types.Scene.ignoreTextureRestrictions = bpy.props.BoolProperty(
		name = 'Ignore Texture Restrictions (Breaks CI Textures)')

	bpy.types.Scene.characterIgnoreSwitch = \
		bpy.props.BoolProperty(name = 'Ignore Switch Nodes', default = True)
	bpy.types.Scene.fullTraceback = \
		bpy.props.BoolProperty(name = 'Show Full Error Traceback', default = False)

# called on add-on disabling
def unregister():
	render_engine_unregister()

	# Camera
	#del bpy.types.Scene.saveCameraSettings
	#del bpy.types.Scene.levelCamera

	del bpy.types.Scene.rotationAxis
	del bpy.types.Scene.rotationAngle
	del bpy.types.Scene.rotationOrder

	# Geolayout
	del bpy.types.Scene.geoExportStart
	del bpy.types.Scene.geoExportEnd
	del bpy.types.Scene.overwriteModelLoad
	del bpy.types.Scene.modelLoadLevelScriptCmd
	del bpy.types.Scene.modelID
	del bpy.types.Scene.textDumpGeo
	del bpy.types.Scene.textDumpGeoPath
	del bpy.types.Scene.geoExportPath
	del bpy.types.Scene.geoUseBank0
	del bpy.types.Scene.geoRAMAddr
	del bpy.types.Scene.geoTexDir
	del bpy.types.Scene.geoSaveTextures
	del bpy.types.Scene.geoSeparateTextureDef
	del bpy.types.Scene.geoInsertableBinaryPath
	del bpy.types.Scene.geoIsSegPtr
	del bpy.types.Scene.geoName
	del bpy.types.Scene.geoGroupName
	del bpy.types.Scene.geoExportHeaderType
	del bpy.types.Scene.geoCustomExport
	del bpy.types.Scene.geoLevelName
	del bpy.types.Scene.geoLevelOption
	del bpy.types.Scene.modifyOldGeo
	del bpy.types.Scene.geoStructName

	# Animation
	del bpy.types.Scene.animStartImport
	del bpy.types.Scene.levelAnimImport
	del bpy.types.Scene.levelAnimExport
	del bpy.types.Scene.isDMAImport
	del bpy.types.Scene.isDMAExport
	del bpy.types.Scene.DMAStartAddress
	del bpy.types.Scene.DMAEntryAddress
	del bpy.types.Scene.loopAnimation
	del bpy.types.Scene.setAnimListIndex
	del bpy.types.Scene.overwrite_0x28
	del bpy.types.Scene.addr_0x27
	del bpy.types.Scene.addr_0x28
	del bpy.types.Scene.animExportPath
	del bpy.types.Scene.animOverwriteDMAEntry
	del bpy.types.Scene.animInsertableBinaryPath
	del bpy.types.Scene.animIsSegPtr
	del bpy.types.Scene.animIsAnimList
	del bpy.types.Scene.animListIndexImport
	del bpy.types.Scene.animListIndexExport
	del bpy.types.Scene.animName
	del bpy.types.Scene.animWriteHeaders
	del bpy.types.Scene.animCustomExport
	del bpy.types.Scene.animExportHeaderType
	del bpy.types.Scene.animLevelName
	del bpy.types.Scene.animLevelOption

	# Character
	del bpy.types.Scene.characterIgnoreSwitch
	del bpy.types.Scene.sm64_character
	del bpy.types.Scene.useFaceAnimation
	del bpy.types.Scene.overwriteWingPositions
	del bpy.types.Scene.generateArmature
	del bpy.types.Scene.geoImportAddr
	del bpy.types.Scene.levelGeoImport
	del bpy.types.Scene.levelGeoExport
	del bpy.types.Scene.ignoreSwitch

	# Display List
	del bpy.types.Scene.levelDLImport
	del bpy.types.Scene.levelDLExport
	del bpy.types.Scene.DLImportStart
	del bpy.types.Scene.DLExportStart
	del bpy.types.Scene.DLExportEnd
	del bpy.types.Scene.DLExportGeoPtr
	del bpy.types.Scene.overwriteGeoPtr
	del bpy.types.Scene.isSegmentedAddrDLImport
	del bpy.types.Scene.DLExportPath
	del bpy.types.Scene.DLExportisStatic
	del bpy.types.Scene.DLDefinePath
	del bpy.types.Scene.DLUseBank0
	del bpy.types.Scene.DLRAMAddr
	del bpy.types.Scene.DLTexDir
	del bpy.types.Scene.DLSaveTextures
	del bpy.types.Scene.DLSeparateTextureDef
	del bpy.types.Scene.DLincludeChildren
	del bpy.types.Scene.DLInsertableBinaryPath
	del bpy.types.Scene.DLName
	del bpy.types.Scene.DLCustomExport
	del bpy.types.Scene.DLExportHeaderType
	del bpy.types.Scene.DLGroupName
	del bpy.types.Scene.DLLevelName
	del bpy.types.Scene.DLLevelOption

	# Level
	del bpy.types.Scene.levelLevel
	del bpy.types.Scene.exportRange
	del bpy.types.Scene.segment4
	del bpy.types.Scene.useCustomSegment4
	del bpy.types.Scene.useLogFile
	del bpy.types.Scene.logFilePath

	del bpy.types.Scene.levelName
	del bpy.types.Scene.levelExportPath 
	del bpy.types.Scene.levelSaveTextures
	#del bpy.types.Scene.levelCamera	
	del bpy.types.Scene.levelCustomExport
	del bpy.types.Scene.levelOption

	# Collision
	del bpy.types.Scene.colExportPath
	del bpy.types.Scene.colExportLevel
	del bpy.types.Scene.addr_0x2A
	del bpy.types.Scene.set_addr_0x2A
	del bpy.types.Scene.colStartAddr
	del bpy.types.Scene.colEndAddr
	del bpy.types.Scene.colInsertableBinaryPath	
	del bpy.types.Scene.colExportRooms
	del bpy.types.Scene.colName
	del bpy.types.Scene.colCustomExport
	del bpy.types.Scene.colExportHeaderType
	del bpy.types.Scene.colLevelName
	del bpy.types.Scene.colLevelOption

	# Texrect
	del bpy.types.Scene.texrect
	del bpy.types.Scene.TexRectExportPath
	del bpy.types.Scene.TexRectTexDir
	del bpy.types.Scene.TexRectSaveTextures
	del bpy.types.Scene.TexRectName
	del bpy.types.Scene.texrectImageTexture
	del bpy.types.Scene.TexRectCustomExport
	del bpy.types.Scene.TexRectExportType

	# ROM
	del bpy.types.Scene.importRom
	del bpy.types.Scene.exportRom
	del bpy.types.Scene.outputRom
	del bpy.types.Scene.extendBank4
	del bpy.types.Scene.convertibleAddr
	del bpy.types.Scene.levelConvert
	del bpy.types.Scene.blenderToN64Scale
	del bpy.types.Scene.fullTraceback
	del bpy.types.Scene.decompPath
	del bpy.types.Scene.disableScroll
	del bpy.types.Scene.ignoreTextureRestrictions

	sm64_spline_unregister()
	level_unregister()
	sm64_obj_unregister()
	mat_unregister()
	bone_unregister()
	col_unregister()
	cam_unregister()
	bsdf_conv_unregister()
	for cls in classes:
		unregister_class(cls)
