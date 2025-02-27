from .utility import *
from .sm64_constants import *
from bpy.utils import register_class, unregister_class
import bpy, bmesh
import os
from io import BytesIO
import math
from .sm64_function_map import func_map
from .sm64_spline import *


enumTerrain = [
	('Custom', 'Custom', 'Custom'),
	('TERRAIN_GRASS', 'Grass', 'Grass'),
	('TERRAIN_STONE', 'Stone', 'Stone'),
	('TERRAIN_SNOW', 'Snow', 'Snow'),
	('TERRAIN_SAND', 'Sand', 'Sand'),
	('TERRAIN_SPOOKY', 'Spooky', 'Spooky'),
	('TERRAIN_WATER', 'Water', 'Water'),
	('TERRAIN_SLIDE', 'Slide', 'Slide'),
]

enumMusicSeq = [
	('Custom', 'Custom', 'Custom'),
	('SEQ_LEVEL_BOSS_KOOPA', 'Boss Koopa', 'Boss Koopa'),
    ('SEQ_LEVEL_BOSS_KOOPA_FINAL', 'Boss Koopa Final', 'Boss Koopa Final'),
    ('SEQ_LEVEL_GRASS', 'Grass Level', 'Grass Level'),
    ('SEQ_LEVEL_HOT', 'Hot Level', 'Hot Level'),
    ('SEQ_LEVEL_INSIDE_CASTLE', 'Inside Castle', 'Inside Castle'),
    ('SEQ_LEVEL_KOOPA_ROAD', 'Koopa Road', 'Koopa Road'),
    ('SEQ_LEVEL_SLIDE', 'Slide Level', 'Slide Level'),
    ('SEQ_LEVEL_SNOW', 'Snow Level', 'Snow Level'),
    ('SEQ_LEVEL_SPOOKY', 'Spooky Level', 'Spooky Level'),
    ('SEQ_LEVEL_UNDERGROUND', 'Underground Level', 'Underground Level'),
    ('SEQ_LEVEL_WATER', 'Water Level', 'Water Level'),
    ('SEQ_MENU_FILE_SELECT', 'File Select', 'File Select'),
    ('SEQ_MENU_STAR_SELECT', 'Star Select Menu', 'Star Select Menu'),
    ('SEQ_MENU_TITLE_SCREEN', 'Title Screen', 'Title Screen'),
    ('SEQ_EVENT_BOSS', 'Boss', 'Boss'),
    ('SEQ_EVENT_CUTSCENE_COLLECT_KEY', 'Collect Key', 'Collect Key'),
    ('SEQ_EVENT_CUTSCENE_COLLECT_STAR', 'Collect Star', 'Collect Star'),
    ('SEQ_EVENT_CUTSCENE_CREDITS', 'Credits', 'Credits'),
    ('SEQ_EVENT_CUTSCENE_ENDING', 'Ending Cutscene', 'Ending Cutscene'),
    ('SEQ_EVENT_CUTSCENE_INTRO', 'Intro Cutscene', 'Intro Cutscene'),
    ('SEQ_EVENT_CUTSCENE_LAKITU', 'Lakitu Cutscene', 'Lakitu Cutscene'),
    ('SEQ_EVENT_CUTSCENE_STAR_SPAWN', 'Star Spawn', 'Star Spawn'),
    ('SEQ_EVENT_CUTSCENE_VICTORY', 'Victory Cutscene', 'Victory Cutscene'),
    ('SEQ_EVENT_ENDLESS_STAIRS', 'Endless Stairs', 'Endless Stairs'),
    ('SEQ_EVENT_HIGH_SCORE', 'High Score', 'High Score'),
    ('SEQ_EVENT_KOOPA_MESSAGE', 'Koopa Message', 'Koopa Message'),
    ('SEQ_EVENT_MERRY_GO_ROUND', 'Merry Go Round', 'Merry Go Round'),
    ('SEQ_EVENT_METAL_CAP', 'Metal Cap', 'Metal Cap'),
    ('SEQ_EVENT_PEACH_MESSAGE', 'Peach Message', 'Peach Message'),
    ('SEQ_EVENT_PIRANHA_PLANT', 'Piranha Lullaby', 'Piranha Lullaby'),
    ('SEQ_EVENT_POWERUP', 'Powerup', 'Powerup'),
    ('SEQ_EVENT_RACE', 'Race', 'Race'),
    ('SEQ_EVENT_SOLVE_PUZZLE', 'Solve Puzzle', 'Solve Puzzle'),
	('SEQ_SOUND_PLAYER', 'Sound Player', 'Sound Player'),
    ('SEQ_EVENT_TOAD_MESSAGE', 'Toad Message', 'Toad Message'),
]

enumWarpType = [
	("Warp", "Warp", "Warp"),
	("Painting", "Painting", "Painting"),
	("Instant", "Instant", "Instant"),
]

enumWarpFlag = [
	("Custom", "Custom", "Custom"),
	("WARP_NO_CHECKPOINT", 'No Checkpoint', 'No Checkpoint'),
	("WARP_CHECKPOINT", 'Checkpoint', 'Checkpoint'),
]

enumEnvFX = [
	('Custom', 'Custom', 'Custom'),
	('ENVFX_MODE_NONE', 'None', 'None'),
	('ENVFX_SNOW_NORMAL', 'Snow', 'Used in CCM, SL'),
	('ENVFX_SNOW_WATER', 'Water Bubbles', 'Used in Secret Aquarium, Sunken Ships'),
	('ENVFX_SNOW_BLIZZARD', 'Blizzard', 'Unused'),
	('ENVFX_FLOWERS', 'Flowers', 'Unused'),
	('ENVFX_LAVA_BUBBLES', 'Lava Bubbles', 'Used in LLL, BitFS, Bowser 2'),
	('ENVFX_WHIRLPOOL_BUBBLES', 'Whirpool Bubbles', 'Used in DDD where whirpool is'),
	('ENVFX_JETSTREAM_BUBBLES', 'Jetstream Bubbles', 'Used in JRB, DDD where jetstream is'),
]

enumCameraMode = [
	('Custom', 'Custom', 'Custom'),
	('CAMERA_MODE_NONE', 'None', 'None'),
	('CAMERA_MODE_RADIAL', 'Radial', 'Radial'),
	('CAMERA_MODE_OUTWARD_RADIAL', 'Outward Radial', 'Outward Radial'),
	('CAMERA_MODE_BEHIND_MARIO', 'Behind Mario', 'Behind Mario'),
	('CAMERA_MODE_CLOSE', 'Close', 'Close'),
	('CAMERA_MODE_C_UP', 'C Up', 'C Up'),
	('CAMERA_MODE_WATER_SURFACE', 'Water Surface', 'Water Surface'),
	('CAMERA_MODE_SLIDE_HOOT', 'Slide/Hoot', 'Slide/Hoot'),
	('CAMERA_MODE_INSIDE_CANNON', 'Inside Cannon', 'Inside Cannon'),
	('CAMERA_MODE_BOSS_FIGHT', 'Boss Fight', 'Boss Fight'),
	('CAMERA_MODE_PARALLEL_TRACKING', 'Parallel Tracking', 'Parallel Tracking'),
	('CAMERA_MODE_FIXED', 'Fixed', 'Fixed'),
	('CAMERA_MODE_8_DIRECTIONS', '8 Directions', '8 Directions'),
	('CAMERA_MODE_FREE_ROAM', 'Free Roam', 'Free Roam'),
	('CAMERA_MODE_SPIRAL_STAIRS', 'Spiral Stairs', 'Spiral Stairs'),
]

enumBackground = [
	('OCEAN_SKY', 'Ocean Sky', 'Ocean Sky'),
	('FLAMING_SKY', 'Flaming Sky', 'Flaming Sky'),
	('UNDERWATER_CITY', 'Underwater City', 'Underwater City'),
	('BELOW_CLOUDS', 'Below Clouds', 'Below Clouds'),
	('SNOW_MOUNTAINS', 'Snow Mountains', 'Snow Mountains'),
	('DESERT', 'Desert', 'Desert'),
	('HAUNTED', 'Haunted', 'Haunted'),
	('GREEN_SKY', 'Green Sky', 'Green Sky'),
	('ABOVE_CLOUDS', 'Above Clouds', 'Above Clouds'),
	('PURPLE_SKY', 'Purple Sky', 'Purple Sky'),
]

backgroundSegments = {
	'OCEAN_SKY' : 'water',
	'FLAMING_SKY' : 'bitfs',
	'UNDERWATER_CITY' : 'wdw',
	'BELOW_CLOUDS' : 'cloud_floor',
	'SNOW_MOUNTAINS' : 'ccm',
	'DESERT' : 'ssl',
	'HAUNTED' : 'bbh',
	'GREEN_SKY' : 'bidw',
	'ABOVE_CLOUDS' : 'clouds',
	'PURPLE_SKY' : 'bits',
}

enumWaterBoxType = [
	("Water", 'Water', "Water"),
	('Toxic Haze', 'Toxic Haze', 'Toxic Haze')
]

# When adding new types related to geolayout,
# Make sure to add exceptions in utility.py - selectMeshChildrenOnly
enumObjectType = [
	('None', 'None', 'None'),
	('Level Root', 'Level Root', 'Level Root'),
	('Area Root', 'Area Root', 'Area Root'),
	('Object', 'Object', 'Object'),
	('Macro', 'Macro', 'Macro'),
	('Special', 'Special', 'Special'),
	('Mario Start', 'Mario Start', 'Mario Start'),
	('Whirlpool', 'Whirlpool', 'Whirlpool'),
	('Water Box', 'Water Box', 'Water Box'),
	('Camera Volume', 'Camera Volume', 'Camera Volume'),
	('Switch', 'Switch Node', 'Switch Node'),
	#('Trajectory', 'Trajectory', 'Trajectory'),
]

class SM64_Object:
	def __init__(self, model, position, rotation, behaviour, bparam, acts):
		self.model = model
		self.behaviour = behaviour
		self.bparam = bparam
		self.acts = acts
		self.position = position
		self.rotation = rotation
	
	def to_c(self):
		if self.acts == 0x1F:
			return 'OBJECT(' + str(self.model) + ', ' + \
				str(int(round(self.position[0]))) + ', ' + \
				str(int(round(self.position[1]))) + ', ' + \
				str(int(round(self.position[2]))) + ', ' + \
				str(int(round(math.degrees(self.rotation[0])))) + ', ' + \
				str(int(round(math.degrees(self.rotation[1])))) + ', ' + \
				str(int(round(math.degrees(self.rotation[2])))) + ', ' + \
				str(self.bparam) + ', ' + str(self.behaviour) + ')'
		else:
			return 'OBJECT_WITH_ACTS(' + str(self.model) + ', ' + \
				str(int(round(self.position[0]))) + ', ' + \
				str(int(round(self.position[1]))) + ', ' + \
				str(int(round(self.position[2]))) + ', ' + \
				str(int(round(math.degrees(self.rotation[0])))) + ', ' + \
				str(int(round(math.degrees(self.rotation[1])))) + ', ' + \
				str(int(round(math.degrees(self.rotation[2])))) + ', ' + \
				str(self.bparam) + ', ' + str(self.behaviour) + ', ' + str(self.acts) + ')'

class SM64_Whirpool:
	def __init__(self, index, condition, strength, position):
		self.index = index
		self.condition = condition
		self.strength = strength
		self.position = position
	
	def to_c(self):
		return 'WHIRPOOL(' + str(self.index) + ', ' +  str(self.condition) + ', ' +\
			str(int(round(self.position[0]))) + ', ' + \
			str(int(round(self.position[1]))) + ', ' + \
			str(int(round(self.position[2]))) + ', ' + \
			str(self.strength) + ')'

class SM64_Macro_Object:
	def __init__(self, preset, position, rotation, bparam):
		self.preset = preset
		self.bparam = bparam
		self.position = position
		self.rotation = rotation
	
	def to_c(self):
		if self.bparam is None:
			return 'MACRO_OBJECT(' + str(self.preset) + ', ' + \
				str(int(round(math.degrees(self.rotation[1])))) + ', ' + \
				str(int(round(self.position[0]))) + ', ' + \
				str(int(round(self.position[1]))) + ', ' + \
				str(int(round(self.position[2]))) + ')'
		else:
			return 'MACRO_OBJECT_WITH_BEH_PARAM(' + str(self.preset) + ', ' + \
				str(int(round(math.degrees(self.rotation[1])))) + ', ' + \
				str(int(round(self.position[0]))) + ', ' + \
				str(int(round(self.position[1]))) + ', ' + \
				str(int(round(self.position[2]))) + ', ' + \
				str(self.bparam) + ')'

class SM64_Special_Object:
	def __init__(self, preset, position, rotation, bparam):
		self.preset = preset
		self.bparam = bparam
		self.position = position
		self.rotation = rotation

	def to_binary(self):
		data = int(self.preset).to_bytes(2, 'big')
		if len(self.position) > 3:
			raise PluginError("Object position should not be " + \
				str(len(self.position) + ' fields long.'))
		for index in self.position:
			data.extend(int(round(index)).to_bytes(2, 'big', signed = False))
		if self.rotation is not None:
			data.extend(int(round(math.degrees(self.rotation[1]))).to_bytes(2, 'big'))
			if self.bparam is not None:
				data.extend(int(self.bparam).to_bytes(2, 'big'))
		return data
	
	def to_c(self):
		if self.rotation is None:
			return 'SPECIAL_OBJECT(' + str(self.preset) + ', ' +\
				str(int(round(self.position[0]))) + ', ' + \
				str(int(round(self.position[1]))) + ', ' + \
				str(int(round(self.position[2]))) + '),\n'
		elif self.bparam is None:
			return 'SPECIAL_OBJECT_WITH_YAW(' + str(self.preset) + ', ' +\
				str(int(round(self.position[0]))) + ', ' + \
				str(int(round(self.position[1]))) + ', ' + \
				str(int(round(self.position[2]))) + ', ' + \
				str(int(round(math.degrees(self.rotation[1])))) + '),\n'
		else:
			return 'SPECIAL_OBJECT_WITH_YAW_AND_PARAM(' + str(self.preset) + ', ' +\
				str(int(round(self.position[0]))) + ', ' + \
				str(int(round(self.position[1]))) + ', ' + \
				str(int(round(self.position[2]))) + ', ' + \
				str(int(round(math.degrees(self.rotation[1])))) + ', ' + \
				str(self.bparam) + '),\n'

class SM64_Mario_Start:
	def __init__(self, area, position, rotation):
		self.area = area
		self.position = position
		self.rotation = rotation
	
	def to_c(self):
		return 'MARIO_POS(' + str(self.area) + ', ' + str(int(round(math.degrees(self.rotation[1])))) + ', ' +\
			str(int(round(self.position[0]))) + ', ' + str(int(round(self.position[1]))) + ', ' + str(int(round(self.position[2]))) + ')'

class SM64_Area:
	def __init__(self, index, music_seq, music_preset, 
		terrain_type, geolayout, collision, warpNodes, name, startDialog):
		self.cameraVolumes = []
		self.name = toAlnum(name)
		self.geolayout = geolayout
		self.collision = collision
		self.index = index
		self.objects = []
		self.macros = []
		self.specials = []
		self.water_boxes = []
		self.music_preset = music_preset
		self.music_seq = music_seq
		self.terrain_type = terrain_type
		self.warpNodes = warpNodes
		self.mario_start = None
		self.splines = []
		self.startDialog = startDialog

	def macros_name(self):
		return self.name + '_macro_objs'

	def to_c_script(self, includeRooms):
		data = ''
		data += '\tAREA(' + str(self.index) + ', ' + self.geolayout.name + '),\n'
		for warpNode in self.warpNodes:
			data += '\t\t' + warpNode + ',\n'
		for obj in self.objects:
			data += '\t\t' + obj.to_c() + ',\n'
		data += '\t\tTERRAIN(' + self.collision.name + '),\n'
		if includeRooms:
			data += '\t\tROOMS(' + self.collision.rooms_name() + '),\n'
		data += '\t\tMACRO_OBJECTS(' + self.macros_name() + '),\n'
		if self.music_seq is None:
			data += '\t\tSTOP_MUSIC(0),\n'
		else:
			data += '\t\tSET_BACKGROUND_MUSIC(' + self.music_preset + ', ' + self.music_seq + '),\n'
		if self.startDialog is not None:
			data += '\t\tSHOW_DIALOG(0x00, ' + self.startDialog + '),\n'
		data += '\t\tTERRAIN_TYPE(' + self.terrain_type + '),\n'
		data += '\tEND_AREA(),\n\n'
		return data

	def to_c_macros(self):
		data = ''
		data += 'const MacroObject ' + self.macros_name() + '[] = {\n'
		for macro in self.macros:
			data += '\t' + macro.to_c() + ',\n'
		data += '\tMACRO_OBJECT_END(),\n};\n\n'

		return data
	
	def to_c_def_macros(self):
		return 'extern const MacroObject ' + self.macros_name() + '[];\n'

	def to_c_camera_volumes(self):
		data = ''
		for camVolume in self.cameraVolumes:
			data +=  '\t' + camVolume.to_c() + '\n'
		return data

	def hasCutsceneSpline(self):
		for spline in self.splines:
			if spline.splineType == 'Cutscene':
				return True
		return False
	
	def to_c_splines(self):
		data = ''
		for spline in self.splines:
			data += spline.to_c() + '\n'
		if self.hasCutsceneSpline():
			data = '#include "src/game/camera.h"\n\n' + data
		return data
	
	def to_c_def_splines(self):
		data = ''
		for spline in self.splines:
			data += spline.to_c_def()
		if self.hasCutsceneSpline():
			data = '#include "src/game/camera.h"\n\n' + data
		return data

class CollisionWaterBox:
	def __init__(self, waterBoxType, position, scale, emptyScale):
		# The scale ordering is due to the fact that scaling happens AFTER rotation.
		# Thus the translation uses Y-up, while the scale uses Z-up.
		self.waterBoxType = waterBoxType
		self.low = (position[0] - scale[0] * emptyScale, position[2] - scale[1] * emptyScale)
		self.high = (position[0] + scale[0] * emptyScale, position[2] + scale[1] * emptyScale)
		self.height = position[1] + scale[2] * emptyScale

	def to_binary(self):
		data = bytearray([0x00, 0x00 if self.waterBoxType == 'Water' else 0x32])
		data.extend(int(round(self.low[0])).to_bytes(2, 'big', signed=True))
		data.extend(int(round(self.low[1])).to_bytes(2, 'big', signed=True))
		data.extend(int(round(self.high[0])).to_bytes(2, 'big', signed=True))
		data.extend(int(round(self.high[1])).to_bytes(2, 'big', signed=True))
		data.extend(int(round(self.height)).to_bytes(2, 'big', signed=True))
		return data
	
	def to_c(self):
		data = 'COL_WATER_BOX(' + \
			('0x00' if self.waterBoxType == 'Water' else '0x32') + ', ' + \
			str(int(round(self.low[0]))) + ', ' + \
			str(int(round(self.low[1]))) + ', ' + \
			str(int(round(self.high[0]))) + ', ' + \
			str(int(round(self.high[1]))) + ', ' + \
			str(int(round(self.height))) + '),\n'
		return data

class CameraVolume:
	def __init__(self, area, functionName, position, rotation, scale, emptyScale):
		# The scale ordering is due to the fact that scaling happens AFTER rotation.
		# Thus the translation uses Y-up, while the scale uses Z-up.
		self.area = area
		self.functionName = functionName
		self.position = position
		self.scale = mathutils.Vector((scale[0], scale[2], scale[1])) * emptyScale
		self.rotation = rotation

	def to_binary(self):
		raise PluginError("Binary exporting not implemented for camera volumens.")
	
	def to_c(self):
		data = '{' + \
			str(self.area) + ', ' + str(self.functionName) + ', ' + \
			str(int(round(self.position[0]))) + ', ' + \
			str(int(round(self.position[1]))) + ', ' + \
			str(int(round(self.position[2]))) + ', ' + \
			str(int(round(self.scale[0]))) + ', ' + \
			str(int(round(self.scale[1]))) + ', ' + \
			str(int(round(self.scale[2]))) + ', ' + \
			str(convertRadiansToS16(self.rotation[1])) + '},'
		return data

def exportAreaCommon(areaObj, transformMatrix, geolayout, collision, name):
	bpy.ops.object.select_all(action = 'DESELECT')
	areaObj.select_set(True)

	if not areaObj.noMusic:
		if areaObj.musicSeqEnum != 'Custom':
			musicSeq = areaObj.musicSeqEnum
		else:
			musicSeq = areaObj.music_seq
	else:
		musicSeq = None

	if areaObj.terrainEnum != 'Custom':
		terrainType = areaObj.terrainEnum
	else:
		terrainType = areaObj.terrain_type

	area = SM64_Area(areaObj.areaIndex, musicSeq, areaObj.music_preset, 
		terrainType, geolayout, collision, 
		[areaObj.warpNodes[i].to_c() for i in range(len(areaObj.warpNodes))],
		name, areaObj.startDialog if areaObj.showStartDialog else None)

	start_process_sm64_objects(areaObj, area, transformMatrix, False)

	return area

# These are all done in reference to refresh 8
def handleRefreshDiffModelIDs(modelID):
	return modelID

def handleRefreshDiffSpecials(preset):
	return preset

def handleRefreshDiffMacros(preset):
	return preset

def start_process_sm64_objects(obj, area, transformMatrix, specialsOnly):
	#spaceRotation = mathutils.Quaternion((1, 0, 0), math.radians(90.0)).to_matrix().to_4x4()

	# We want translations to be relative to area obj, but rotation/scale to be world space
	translation, rotation, scale = obj.matrix_world.decompose()
	process_sm64_objects(obj, area, 
		mathutils.Matrix.Translation(translation), transformMatrix, specialsOnly)

def process_sm64_objects(obj, area, rootMatrix, transformMatrix, specialsOnly):
	translation, originalRotation, scale = \
			(transformMatrix @ rootMatrix.inverted() @ obj.matrix_world).decompose()

	finalTransform = mathutils.Matrix.Translation(translation) @ \
		originalRotation.to_matrix().to_4x4() @ \
		mathutils.Matrix.Diagonal(scale).to_4x4()

	# Hacky solution to handle Z-up to Y-up conversion
	rotation = originalRotation @ mathutils.Quaternion((1, 0, 0), math.radians(90.0))

	if obj.data is None:
		if obj.sm64_obj_type == 'Area Root' and obj.areaIndex != area.index:
			return
		if specialsOnly:
			if obj.sm64_obj_type == 'Special':
				preset = obj.sm64_special_enum if obj.sm64_special_enum != 'Custom' else obj.sm64_obj_preset
				preset = handleRefreshDiffSpecials(preset)
				area.specials.append(SM64_Special_Object(preset, translation, 
					rotation.to_euler() if obj.sm64_obj_set_yaw else None, 
					obj.sm64_obj_bparam if (obj.sm64_obj_set_yaw and obj.sm64_obj_set_bparam) else None))
			elif obj.sm64_obj_type == 'Water Box':
				checkIdentityRotation(obj, rotation, False)
				area.water_boxes.append(CollisionWaterBox(obj.waterBoxType, 
					translation, scale, obj.empty_display_size))
		else:
			if obj.sm64_obj_type == 'Object':
				modelID = obj.sm64_model_enum if obj.sm64_model_enum != 'Custom' else obj.sm64_obj_model
				modelID = handleRefreshDiffModelIDs(modelID)
				behaviour = obj.sm64_obj_behaviour
				area.objects.append(SM64_Object(modelID, translation, rotation.to_euler(), 
					behaviour, obj.sm64_obj_bparam, get_act_string(obj)))
			elif obj.sm64_obj_type == 'Macro':
				macro = obj.sm64_macro_enum if obj.sm64_macro_enum != 'Custom' else obj.sm64_obj_preset
				area.macros.append(SM64_Macro_Object(macro, translation, rotation.to_euler(), 
					obj.sm64_obj_bparam if obj.sm64_obj_set_bparam else None))
			elif obj.sm64_obj_type == 'Mario Start':
				mario_start = SM64_Mario_Start(obj.sm64_obj_mario_start_area, translation, rotation.to_euler())
				area.objects.append(mario_start)
				area.mario_start = mario_start
			elif obj.sm64_obj_type == 'Trajectory':
				pass
			elif obj.sm64_obj_type == 'Whirpool':
				area.objects.append(SM64_Whirpool(obj.whirlpool_index, 
					obj.whirpool_condition, obj.whirpool_strength, translation))
			elif obj.sm64_obj_type == 'Camera Volume':
				checkIdentityRotation(obj, rotation, True)
				if obj.cameraVolumeGlobal:
					triggerIndex = -1
				else:
					triggerIndex = area.index
				area.cameraVolumes.append(CameraVolume(triggerIndex, obj.cameraVolumeFunction,
					translation, rotation.to_euler(), scale, obj.empty_display_size))

	elif not specialsOnly and isCurveValid(obj):
		area.splines.append(convertSplineObject(area.name + '_spline_' + obj.name , obj, finalTransform))
			

	for child in obj.children:
		process_sm64_objects(child, area, rootMatrix, transformMatrix, specialsOnly)

def get_act_string(obj):
	if obj.sm64_obj_use_act1 and obj.sm64_obj_use_act2 and obj.sm64_obj_use_act3 and \
		obj.sm64_obj_use_act4 and obj.sm64_obj_use_act5 and obj.sm64_obj_use_act6:
		return 0x1F
	else:
		data = ''
		if obj.sm64_obj_use_act1:
			data += (" | " if len(data) > 0 else '') + 'ACT_1'
		if obj.sm64_obj_use_act2:
			data += (" | " if len(data) > 0 else '') + 'ACT_2'
		if obj.sm64_obj_use_act3:
			data += (" | " if len(data) > 0 else '') + 'ACT_3'
		if obj.sm64_obj_use_act4:
			data += (" | " if len(data) > 0 else '') + 'ACT_4'
		if obj.sm64_obj_use_act5:
			data += (" | " if len(data) > 0 else '') + 'ACT_5'
		if obj.sm64_obj_use_act6:
			data += (" | " if len(data) > 0 else '') + 'ACT_6'
		return data

class SearchModelIDEnumOperator(bpy.types.Operator):
	bl_idname = "object.search_model_id_enum_operator"
	bl_label = "Search Model IDs"
	bl_property = "sm64_model_enum"
	bl_options = {'REGISTER', 'UNDO'} 

	sm64_model_enum = bpy.props.EnumProperty(items = enumModelIDs)

	def execute(self, context):
		context.object.sm64_model_enum = self.sm64_model_enum
		bpy.context.region.tag_redraw()
		self.report({'INFO'}, "Selected: " + self.sm64_model_enum)
		return {'FINISHED'}

	def invoke(self, context, event):
		context.window_manager.invoke_search_popup(self)
		return {'RUNNING_MODAL'}

class SearchBehaviourEnumOperator(bpy.types.Operator):
	bl_idname = "object.search_behaviour_enum_operator"
	bl_label = "Search Behaviours"
	bl_property = "sm64_behaviour_enum"
	bl_options = {'REGISTER', 'UNDO'} 

	sm64_behaviour_enum = bpy.props.EnumProperty(items = enumBehaviourPresets)

	def execute(self, context):
		context.object.sm64_behaviour_enum = self.sm64_behaviour_enum
		bpy.context.region.tag_redraw()
		self.report({'INFO'}, "Selected: " + sm64_behaviour_enum)
		return {'FINISHED'}

	def invoke(self, context, event):
		context.window_manager.invoke_search_popup(self)
		return {'RUNNING_MODAL'}

class SearchMacroEnumOperator(bpy.types.Operator):
	bl_idname = "object.search_macro_enum_operator"
	bl_label = "Search Macros"
	bl_property = "sm64_macro_enum"
	bl_options = {'REGISTER', 'UNDO'} 

	sm64_macro_enum = bpy.props.EnumProperty(items = enumMacrosNames)

	def execute(self, context):
		context.object.sm64_macro_enum = self.sm64_macro_enum
		bpy.context.region.tag_redraw()
		self.report({'INFO'}, "Selected: " + self.sm64_macro_enum)
		return {'FINISHED'}

	def invoke(self, context, event):
		context.window_manager.invoke_search_popup(self)
		return {'RUNNING_MODAL'}

class SearchSpecialEnumOperator(bpy.types.Operator):
	bl_idname = "object.search_special_enum_operator"
	bl_label = "Search Specials"
	bl_property = "sm64_special_enum"
	bl_options = {'REGISTER', 'UNDO'} 

	sm64_special_enum = bpy.props.EnumProperty(items = enumSpecialsNames)

	def execute(self, context):
		context.object.sm64_special_enum = self.sm64_special_enum
		bpy.context.region.tag_redraw()
		self.report({'INFO'}, "Selected: " + self.sm64_special_enum)
		return {'FINISHED'}

	def invoke(self, context, event):
		context.window_manager.invoke_search_popup(self)
		return {'RUNNING_MODAL'}

class SM64ObjectPanel(bpy.types.Panel):
	bl_label = "Object Inspector"
	bl_idname = "SM64_Object_Inspector"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "object"
	bl_options = {'HIDE_HEADER'} 

	@classmethod
	def poll(cls, context):
		return (context.object is not None and context.object.data is None)

	def draw(self, context):
		box = self.layout.box()
		box.box().label(text = 'SM64 Object Inspector')
		obj = context.object
		prop_split(box, obj, 'sm64_obj_type', 'Object Type')
		if obj.sm64_obj_type == 'Object':
			prop_split(box, obj, 'sm64_model_enum', 'Model')
			if obj.sm64_model_enum == 'Custom':
				prop_split(box, obj, 'sm64_obj_model', 'Model ID')
			box.operator(SearchModelIDEnumOperator.bl_idname, icon = 'VIEWZOOM')
			box.box().label(text = 'Model IDs defined in include/model_ids.h.')
			prop_split(box, obj, 'sm64_behaviour_enum', 'Behaviour')
			if obj.sm64_behaviour_enum == 'Custom':
				prop_split(box, obj, 'sm64_obj_behaviour', 'Behaviour Name')
			box.operator(SearchBehaviourEnumOperator.bl_idname, icon = 'VIEWZOOM')
			behaviourLabel = box.box()
			behaviourLabel.label(text = 'Behaviours defined in include/behaviour_data.h.')
			behaviourLabel.label(text = 'Actual contents in data/behaviour_data.c.')
			prop_split(box, obj, 'sm64_obj_bparam', 'Behaviour Parameter')
			self.draw_acts(obj, box)

		elif obj.sm64_obj_type == 'Macro':
			prop_split(box, obj, 'sm64_macro_enum', 'Preset')
			if obj.sm64_macro_enum == 'Custom':
				prop_split(box, obj, 'sm64_obj_preset', 'Preset Name')
			box.operator(SearchMacroEnumOperator.bl_idname, icon = 'VIEWZOOM')
			box.box().label(text = 'Macro presets defined in include/macro_preset_names.h.')
			box.prop(obj, 'sm64_obj_set_bparam', text = 'Set Behaviour Parameter')
			if obj.sm64_obj_set_bparam:
				prop_split(box, obj, 'sm64_obj_bparam', 'Behaviour Parameter')
				
		elif obj.sm64_obj_type == 'Special':
			prop_split(box, obj, 'sm64_special_enum', 'Preset')
			if obj.sm64_special_enum == 'Custom':
				prop_split(box, obj, 'sm64_obj_preset', 'Preset Name')
			box.operator(SearchSpecialEnumOperator.bl_idname, icon = 'VIEWZOOM')
			box.box().label(text = 'Special presets defined in include/special_preset_names.h.')
			box.prop(obj, 'sm64_obj_set_yaw', text = 'Set Yaw')
			if obj.sm64_obj_set_yaw:
				box.prop(obj, 'sm64_obj_set_bparam', text = 'Set Behaviour Parameter')
				if obj.sm64_obj_set_bparam:
					prop_split(box, obj, 'sm64_obj_bparam', 'Behaviour Parameter')

		elif obj.sm64_obj_type == 'Mario Start':
			prop_split(box, obj, 'sm64_obj_mario_start_area', 'Area')

		elif obj.sm64_obj_type == 'Trajectory':
			pass

		elif obj.sm64_obj_type == 'Whirlpool':
			prop_split(box, obj, 'whirpool_index', 'Index')
			prop_split(box, obj, 'whirpool_condition', 'Condition')
			prop_split(box, obj, 'whirpool_strength', 'Strength')
			pass

		elif obj.sm64_obj_type == 'Water Box':
			prop_split(box, obj, 'waterBoxType', 'Water Box Type')
			box.box().label(text = "Water box area defined by top face of box shaped empty.")
			box.box().label(text = "No rotation allowed.")

		elif obj.sm64_obj_type == 'Level Root':
			if obj.useBackgroundColor:
				prop_split(box, obj, 'backgroundColor', 'Background Color')
				box.prop(obj, 'useBackgroundColor')
			else:
				#prop_split(box, obj, 'backgroundID', 'Background ID')
				prop_split(box, obj, 'background', 'Background')
				box.prop(obj, 'useBackgroundColor')
				#box.box().label(text = 'Background IDs defined in include/geo_commands.h.')
			box.prop(obj, 'actSelectorIgnore')
			box.prop(obj, 'setAsStartLevel')
			prop_split(box, obj, 'acousticReach', 'Acoustic Reach')			
			obj.starGetCutscenes.draw(box)

		elif obj.sm64_obj_type == 'Area Root':
			# Code that used to be in area inspector
			prop_split(box, obj, 'areaIndex', 'Area Index')
			box.prop(obj, 'noMusic', text = 'Disable Music')
			if not obj.noMusic:
				prop_split(box, obj, 'music_preset', 'Music Preset')
				prop_split(box, obj, 'musicSeqEnum', 'Music Sequence')
				if obj.musicSeqEnum == 'Custom':
					prop_split(box, obj, 'music_seq', '')
				
			prop_split(box, obj, 'terrainEnum', 'Terrain')
			if obj.terrainEnum == 'Custom':
				prop_split(box, obj, 'terrain_type', '')
			prop_split(box, obj, 'envOption', 'Environment Type')
			if obj.envOption == 'Custom':
				prop_split(box, obj, 'envType', "")
			prop_split(box, obj, 'camOption', 'Camera Type')
			if obj.camOption == 'Custom':
				prop_split(box, obj, 'camType', '')
			camBox = box.box()
			camBox.label(text = 'Warning: Camera modes can be overriden by area specific camera code.')
			camBox.label(text = 'Check the switch statment in camera_course_processing() in src/game/camera.c.')

			fogBox = box.box()
			fogInfoBox = fogBox.box()
			fogInfoBox.label(text = 'Warning: Fog only applies to materials that:')
			fogInfoBox.label(text = '- use fog')
			fogInfoBox.label(text = '- have global fog enabled.')
			prop_split(fogBox, obj, 'area_fog_color', 'Area Fog Color')
			prop_split(fogBox, obj, 'area_fog_position', 'Area Fog Position')

			if obj.areaIndex == 1 or obj.areaIndex == 2 or obj.areaIndex == 3:
				prop_split(box, obj, 'echoLevel', 'Echo Level')
			
			if obj.areaIndex == 1 or obj.areaIndex == 2 or obj.areaIndex == 3 or obj.areaIndex == 4:
				box.prop(obj, 'zoomOutOnPause')
			
			box.prop(obj, 'areaOverrideBG')
			if obj.areaOverrideBG:
				prop_split(box, obj, 'areaBGColor', 'Background Color')
			box.prop(obj, 'showStartDialog')
			if obj.showStartDialog:
				prop_split(box, obj, 'startDialog', "Start Dialog")
				dialogBox = box.box()
				dialogBox.label(text = 'See text/us/dialogs.h for values.')
				dialogBox.label(text = 'See load_level_init_text() in src/game/level_update.c for conditions.')
			box.prop(obj, 'enableRoomSwitch')
			if obj.enableRoomSwitch:
				infoBox = box.box()
				infoBox.label(text = 'Every child hierarchy of the area root will be treated as its own room.')
				infoBox.label(text = 'You can use empties with the "None" type as empty geolayout nodes to group related geometry under.')
				infoBox.label(text = 'Children will ordered alphabetically.')
			box.prop(obj, 'useDefaultScreenRect')
			if not obj.useDefaultScreenRect:
				prop_split(box, obj, 'screenPos', 'Screen Position')
				prop_split(box, obj, 'screenSize', 'Screen Size')
		
			prop_split(box, obj, 'clipPlanes', 'Clip Planes')

			box.label(text = "Warp Nodes")
			box.operator(AddWarpNode.bl_idname).option = len(obj.warpNodes)
			for i in range(len(obj.warpNodes)):
				drawWarpNodeProperty(box, obj.warpNodes[i], i)

		elif obj.sm64_obj_type == 'Camera Volume':
			prop_split(box, obj, 'cameraVolumeFunction', 'Camera Function')
			box.prop(obj, 'cameraVolumeGlobal')
			box.box().label(text = "Only vertical axis rotation allowed.")
		
		elif obj.sm64_obj_type == 'Switch':
			prop_split(box, obj, 'switchFunc', 'Function')
			prop_split(box, obj, 'switchParam', 'Parameter')
			box.box().label(text = 'Children will ordered alphabetically.')
		
		elif obj.sm64_obj_type == 'None':
			box.box().label(text = 'This can be used as an empty transform node in a geolayout hierarchy.')

	def draw_acts(self, obj, layout):
		layout.label(text = 'Acts')
		acts = layout.row()
		self.draw_act(obj, acts, 1)
		self.draw_act(obj, acts, 2)
		self.draw_act(obj, acts, 3)
		self.draw_act(obj, acts, 4)
		self.draw_act(obj, acts, 5)
		self.draw_act(obj, acts, 6)

	def draw_act(self, obj, layout, value):
		layout = layout.column()
		layout.label(text = str(value))
		layout.prop(obj, 'sm64_obj_use_act' + str(value), text = '')

enumStarGetCutscene = [
	('Custom', 'Custom', 'Custom'),
	('0', 'Lakitu Flies Away', 'Lakitu Flies Away'),
	('1', 'Rotate Around Mario', 'Rotate Around Mario'),
	('2', 'Closeup Of Mario', 'Closeup Of Mario'),
	('3', 'Bowser Keys', 'Bowser Keys'),
	('4', '100 Coin Star', '100 Coin Star'),
]

class WarpNodeProperty(bpy.types.PropertyGroup):
	warpType : bpy.props.EnumProperty(name = 'Warp Type', items = enumWarpType, default = 'Warp')
	warpID : bpy.props.StringProperty(name = 'Warp ID', default = '0x0A')
	destLevelEnum : bpy.props.EnumProperty(name = 'Destination Level', default = 'bob', items = enumLevelNames)
	destLevel : bpy.props.StringProperty(name = 'Destination Level Value', default = 'LEVEL_BOB')
	destArea : bpy.props.StringProperty(name = 'Destination Area', default = '0x01')
	destNode : bpy.props.StringProperty(name = 'Destination Node', default = '0x0A')
	warpFlags : bpy.props.StringProperty(name = 'Warp Flags', default = 'WARP_NO_CHECKPOINT')
	warpFlagEnum : bpy.props.EnumProperty(name = 'Warp Flags Value', default = 'WARP_NO_CHECKPOINT', items = enumWarpFlag)
	instantOffset : bpy.props.IntVectorProperty(name = 'Offset',
		size = 3, default = (0,0,0))

	expand : bpy.props.BoolProperty()

	def to_c(self):
		if self.warpType == 'Instant':
			return 'INSTANT_WARP(' + str(self.warpID) + ', ' + str(self.destArea) +\
				', ' + str(self.instantOffset[0]) + ', ' + str(self.instantOffset[1]) + \
				', ' + str(self.instantOffset[2]) + ')'
		else:
			if self.warpType == 'Warp':
				cmd = 'WARP_NODE'
			elif self.warpType == 'Painting':
				cmd = 'PAINTING_WARP_NODE'

			if self.destLevelEnum == 'custom':
				destLevel = self.destLevel
			else:
				destLevel = levelIDNames[self.destLevelEnum]

			if self.warpFlagEnum == 'Custom':
				warpFlags = self.warpFlags
			else:
				warpFlags = self.warpFlagEnum
			return cmd + '(' + str(self.warpID) + ', ' + str(destLevel) + ', ' +\
				str(self.destArea) + ', ' + str(self.destNode) + ', ' + str(warpFlags) + ')'

class AddWarpNode(bpy.types.Operator):
	bl_idname = 'bone.add_warp_node'
	bl_label = 'Add Warp Node'
	bl_options = {'REGISTER', 'UNDO'} 
	option : bpy.props.IntProperty()
	def execute(self, context):
		obj = context.object
		obj.warpNodes.add()
		obj.warpNodes.move(len(obj.warpNodes)-1, self.option)
		self.report({'INFO'}, 'Success!')
		return {'FINISHED'} 

class RemoveWarpNode(bpy.types.Operator):
	bl_idname = 'bone.remove_warp_node'
	bl_label = 'Remove Warp Node'
	bl_options = {'REGISTER', 'UNDO'} 
	option : bpy.props.IntProperty()
	def execute(self, context):
		context.object.warpNodes.remove(self.option)
		self.report({'INFO'}, 'Success!')
		return {'FINISHED'} 

def drawWarpNodeProperty(layout, warpNode, index):
	box = layout.box()
	#box.box().label(text = 'Switch Option ' + str(index + 1))
	box.prop(warpNode, 'expand', text = 'Warp Node ' + \
		str(warpNode.warpID), icon = 'TRIA_DOWN' if warpNode.expand else \
		'TRIA_RIGHT')
	if warpNode.expand:
		prop_split(box, warpNode, 'warpType', 'Warp Type')
		if warpNode.warpType == 'Instant':
			prop_split(box, warpNode, 'warpID', 'Warp ID')
			prop_split(box, warpNode, 'destArea', 'Destination Area')
			prop_split(box, warpNode, 'instantOffset', 'Offset')
		else:
			prop_split(box, warpNode, 'warpID', 'Warp ID')
			prop_split(box, warpNode, 'destLevelEnum', 'Destination Level')
			if warpNode.destLevelEnum == 'custom':
				prop_split(box, warpNode, 'destLevel', '')
			prop_split(box, warpNode, 'destArea', 'Destination Area')
			prop_split(box, warpNode, 'destNode', 'Destination Node')
			prop_split(box, warpNode, 'warpFlagEnum', 'Warp Flags')
			if warpNode.warpFlagEnum == 'Custom':
				prop_split(box, warpNode, 'warpFlags', 'Warp Flags Value')
		
		buttons = box.row(align = True)
		buttons.operator(RemoveWarpNode.bl_idname,
			text = 'Remove Option').option = index
		buttons.operator(AddWarpNode.bl_idname, 
			text = 'Add Option').option = index + 1


class StarGetCutscenesProperty(bpy.types.PropertyGroup):
	star1_option : bpy.props.EnumProperty(items = enumStarGetCutscene, default = '4', name = '1')
	star2_option : bpy.props.EnumProperty(items = enumStarGetCutscene, default = '4', name = '2')
	star3_option : bpy.props.EnumProperty(items = enumStarGetCutscene, default = '4', name = '3')
	star4_option : bpy.props.EnumProperty(items = enumStarGetCutscene, default = '4', name = '4')
	star5_option : bpy.props.EnumProperty(items = enumStarGetCutscene, default = '4', name = '5')
	star6_option : bpy.props.EnumProperty(items = enumStarGetCutscene, default = '4', name = '6')
	star7_option : bpy.props.EnumProperty(items = enumStarGetCutscene, default = '4', name = '7')

	star1_value : bpy.props.IntProperty(default = 0, min = 0, max = 15, name = 'Value')
	star2_value : bpy.props.IntProperty(default = 0, min = 0, max = 15, name = 'Value')
	star3_value : bpy.props.IntProperty(default = 0, min = 0, max = 15, name = 'Value')
	star4_value : bpy.props.IntProperty(default = 0, min = 0, max = 15, name = 'Value')
	star5_value : bpy.props.IntProperty(default = 0, min = 0, max = 15, name = 'Value')
	star6_value : bpy.props.IntProperty(default = 0, min = 0, max = 15, name = 'Value')
	star7_value : bpy.props.IntProperty(default = 0, min = 0, max = 15, name = 'Value')

	def value(self):
		value = '0x'
		value += self.star1_option if self.star1_option != 'Custom' else format(self.star1_value, 'X')
		value += self.star2_option if self.star2_option != 'Custom' else format(self.star2_value, 'X')
		value += self.star3_option if self.star3_option != 'Custom' else format(self.star3_value, 'X')
		value += self.star4_option if self.star4_option != 'Custom' else format(self.star4_value, 'X')
		value += self.star5_option if self.star5_option != 'Custom' else format(self.star5_value, 'X')
		value += self.star6_option if self.star6_option != 'Custom' else format(self.star6_value, 'X')
		value += self.star7_option if self.star7_option != 'Custom' else format(self.star7_value, 'X')
		value += '0'
		return value

	def draw(self, layout):
		layout.label(text = 'Star Get Cutscenes')
		layout.prop(self, 'star1_option')
		if self.star1_option == 'Custom':
			prop_split(layout, self, 'star1_value', '')
		layout.prop(self, 'star2_option')
		if self.star2_option == 'Custom':
			prop_split(layout, self, 'star2_value', '')
		layout.prop(self, 'star3_option')
		if self.star3_option == 'Custom':
			prop_split(layout, self, 'star3_value', '')
		layout.prop(self, 'star4_option')
		if self.star4_option == 'Custom':
			prop_split(layout, self, 'star4_value', '')
		layout.prop(self, 'star5_option')
		if self.star5_option == 'Custom':
			prop_split(layout, self, 'star5_value', '')
		layout.prop(self, 'star6_option')
		if self.star6_option == 'Custom':
			prop_split(layout, self, 'star6_value', '')
		layout.prop(self, 'star7_option')
		if self.star7_option == 'Custom':
			prop_split(layout, self, 'star7_value', '')

def onUpdateObjectType(self, context):
	if self.sm64_obj_type == 'Water Box':
		self.empty_display_type = "CUBE"

sm64_obj_classes = (
	WarpNodeProperty,
	AddWarpNode,
	RemoveWarpNode,

	SearchModelIDEnumOperator,
	SearchBehaviourEnumOperator,
	SearchSpecialEnumOperator,
	SearchMacroEnumOperator,
	SM64ObjectPanel,
	StarGetCutscenesProperty,
)

def sm64_obj_register():
	for cls in sm64_obj_classes:
		register_class(cls)

	bpy.types.Object.sm64_model_enum = bpy.props.EnumProperty(
		name = 'Model', items = enumModelIDs)

	bpy.types.Object.sm64_macro_enum = bpy.props.EnumProperty(
		name = 'Macro', items = enumMacrosNames)

	bpy.types.Object.sm64_special_enum = bpy.props.EnumProperty(
		name = 'Special', items = enumSpecialsNames)

	bpy.types.Object.sm64_behaviour_enum = bpy.props.EnumProperty(
		name = 'Behaviour', items = enumBehaviourPresets)

	#bpy.types.Object.sm64_model = bpy.props.StringProperty(
	#	name = 'Model Name')
	#bpy.types.Object.sm64_macro = bpy.props.StringProperty(
	#	name = 'Macro Name')
	#bpy.types.Object.sm64_special = bpy.props.StringProperty(
	#	name = 'Special Name')
	#bpy.types.Object.sm64_behaviour = bpy.props.StringProperty(
	#	name = 'Behaviour Name')
	
	bpy.types.Object.sm64_obj_type = bpy.props.EnumProperty(
		name = 'SM64 Object Type', items = enumObjectType, default = 'None', update = onUpdateObjectType)
	
	bpy.types.Object.sm64_obj_model = bpy.props.StringProperty(
		name = 'Model', default = 'MODEL_NONE')

	bpy.types.Object.sm64_obj_preset = bpy.props.StringProperty(
		name = 'Preset')

	bpy.types.Object.sm64_obj_bparam = bpy.props.StringProperty(
		name = 'Behaviour Parameter', default = '0x00000000')

	bpy.types.Object.sm64_obj_behaviour = bpy.props.StringProperty(
		name = 'Behaviour')

	bpy.types.Object.sm64_obj_mario_start_area = bpy.props.StringProperty(
		name = 'Area', default = '0x01')

	bpy.types.Object.whirpool_index = bpy.props.StringProperty(
		name = 'Index', default = '0')
	bpy.types.Object.whirpool_condition = bpy.props.StringProperty(
		name = 'Condition', default = '3')
	bpy.types.Object.whirpool_strength = bpy.props.StringProperty(
		name = 'Strength', default = '-30')
	bpy.types.Object.waterBoxType = bpy.props.EnumProperty(
		name = 'Water Box Type', items = enumWaterBoxType, default = 'Water')

	bpy.types.Object.sm64_obj_use_act1 = bpy.props.BoolProperty(
		name = 'Act 1', default = True)
	bpy.types.Object.sm64_obj_use_act2 = bpy.props.BoolProperty(
		name = 'Act 2', default = True)
	bpy.types.Object.sm64_obj_use_act3 = bpy.props.BoolProperty(
		name = 'Act 3', default = True)
	bpy.types.Object.sm64_obj_use_act4 = bpy.props.BoolProperty(
		name = 'Act 4', default = True)
	bpy.types.Object.sm64_obj_use_act5 = bpy.props.BoolProperty(
		name = 'Act 5', default = True)
	bpy.types.Object.sm64_obj_use_act6 = bpy.props.BoolProperty(
		name = 'Act 6', default = True)

	bpy.types.Object.sm64_obj_set_bparam = bpy.props.BoolProperty(
		name = 'Set Behaviour Parameter', default = True)
	
	bpy.types.Object.sm64_obj_set_yaw = bpy.props.BoolProperty(
		name = 'Set Yaw', default = False)
	
	bpy.types.Object.useBackgroundColor = bpy.props.BoolProperty(
		name = 'Use Solid Color For Background', default = False)

	#bpy.types.Object.backgroundID = bpy.props.StringProperty(
	#	name = 'Background ID', default = 'BACKGROUND_OCEAN_SKY')

	bpy.types.Object.background = bpy.props.EnumProperty(
		name = 'Background', items = enumBackground, default = 'OCEAN_SKY')
	
	bpy.types.Object.backgroundColor = bpy.props.FloatVectorProperty(
		name = 'Background Color', subtype='COLOR', size = 4, 
		min = 0, max = 1, default = (0,0,0,1))

	bpy.types.Object.screenPos = bpy.props.IntVectorProperty(
		name = 'Screen Position', size = 2, default = (160, 120), 
		min = -2**15, max = 2**15 - 1)

	bpy.types.Object.screenSize = bpy.props.IntVectorProperty(
		name = 'Screen Size', size = 2, default = (160, 120), 
		min = -2**15, max = 2**15 - 1)

	bpy.types.Object.useDefaultScreenRect = bpy.props.BoolProperty(
		name = 'Use Default Screen Rect', default = True)

	bpy.types.Object.clipPlanes = bpy.props.IntVectorProperty(
		name = 'Clip Planes', size = 2, min = 0, default = (100, 30000)
	)

	bpy.types.Object.area_fog_color = bpy.props.FloatVectorProperty(
		name = 'Area Fog Color', subtype='COLOR', size = 4, 
		min = 0, max = 1, default = (0,0,0,1))

	bpy.types.Object.area_fog_position = bpy.props.FloatVectorProperty(
		name = 'Area Fog Position', size = 2, default = (970, 1000))

	bpy.types.Object.areaOverrideBG = bpy.props.BoolProperty(
		name = 'Override Background')

	bpy.types.Object.areaBGColor = bpy.props.FloatVectorProperty(
		name = 'Background Color', subtype='COLOR', size = 4, 
		min = 0, max = 1, default = (0,0,0,1))

	bpy.types.Object.camOption = bpy.props.EnumProperty(
		items = enumCameraMode, default = 'CAMERA_MODE_8_DIRECTIONS')

	bpy.types.Object.camType = bpy.props.StringProperty(
		name = 'Camera Type', default = 'CAMERA_MODE_8_DIRECTIONS')

	bpy.types.Object.envOption = bpy.props.EnumProperty(
		items = enumEnvFX, default = 'ENVFX_MODE_NONE')

	bpy.types.Object.envType = bpy.props.StringProperty(
		name = 'Environment Type', default = 'ENVFX_MODE_NONE')

	bpy.types.Object.fov = bpy.props.FloatProperty(
		name = 'Field Of View', min = 0, max = 180, default = 45
	)

	bpy.types.Object.dynamicFOV = bpy.props.BoolProperty(
		name = 'Dynamic FOV', default = True)

	bpy.types.Object.cameraVolumeFunction = bpy.props.StringProperty(
		name = 'Camera Function', default = 'cam_castle_hmc_start_pool_cutscene')
	bpy.types.Object.cameraVolumeGlobal = bpy.props.BoolProperty(
		name = 'Is Global')

	bpy.types.Object.starGetCutscenes = bpy.props.PointerProperty(
		name = "Star Get Cutscenes", type = StarGetCutscenesProperty)

	bpy.types.Object.acousticReach = bpy.props.StringProperty(
		name = 'Acoustic Reach', default = '20000')
	
	bpy.types.Object.echoLevel = bpy.props.StringProperty(
		name = 'Echo Level', default = '0x00')

	bpy.types.Object.zoomOutOnPause = bpy.props.BoolProperty(
		name = 'Zoom Out On Pause', default = True)

	bpy.types.Object.areaIndex = bpy.props.IntProperty(name = 'Index',
		min = 1, default = 1)

	bpy.types.Object.music_preset = bpy.props.StringProperty(
		name = "Music Preset", default = '0x00')
	bpy.types.Object.music_seq = bpy.props.StringProperty(
		name = "Music Sequence Value", default = 'SEQ_LEVEL_GRASS')
	bpy.types.Object.noMusic = bpy.props.BoolProperty(
		name = 'No Music', default = False)
	bpy.types.Object.terrain_type = bpy.props.StringProperty(
		name = "Terrain Type", default = 'TERRAIN_GRASS')
	bpy.types.Object.terrainEnum = bpy.props.EnumProperty(
		name = 'Terrain', items = enumTerrain, default = "TERRAIN_GRASS")
	bpy.types.Object.musicSeqEnum = bpy.props.EnumProperty(
		name = 'Music Sequence', items = enumMusicSeq, default = "SEQ_LEVEL_GRASS")

	bpy.types.Object.areaCamera = bpy.props.PointerProperty(type = bpy.types.Camera)
	bpy.types.Object.warpNodes = bpy.props.CollectionProperty(
		type = WarpNodeProperty)

	bpy.types.Object.showStartDialog = bpy.props.BoolProperty(name = "Show Start Dialog")
	bpy.types.Object.startDialog = bpy.props.StringProperty(name = 'Start Dialog', default = 'DIALOG_000')
	bpy.types.Object.actSelectorIgnore = bpy.props.BoolProperty(name = 'Skip Act Selector')
	bpy.types.Object.setAsStartLevel = bpy.props.BoolProperty(name = 'Set As Start Level')

	bpy.types.Object.switchFunc = bpy.props.StringProperty(
		name = 'Function', default = '', 
		description = 'Name of function for C, hex address for binary.')
	
	bpy.types.Object.switchParam = bpy.props.IntProperty(
		name = 'Function Parameter', min = -2**(15), max = 2**(15) - 1, default = 0)
	
	bpy.types.Object.enableRoomSwitch = bpy.props.BoolProperty(name = 'Enable Room System')

def sm64_obj_unregister():
	del bpy.types.Object.sm64_model_enum
	del bpy.types.Object.sm64_macro_enum
	del bpy.types.Object.sm64_special_enum
	del bpy.types.Object.sm64_behaviour_enum

	#del bpy.types.Object.sm64_model
	#del bpy.types.Object.sm64_macro
	#del bpy.types.Object.sm64_special
	#del bpy.types.Object.sm64_behaviour
	
	del bpy.types.Object.sm64_obj_type
	del bpy.types.Object.sm64_obj_model
	del bpy.types.Object.sm64_obj_preset
	del bpy.types.Object.sm64_obj_bparam
	del bpy.types.Object.sm64_obj_behaviour

	del bpy.types.Object.whirpool_index
	del bpy.types.Object.whirpool_condition
	del bpy.types.Object.whirpool_strength

	del bpy.types.Object.waterBoxType

	del bpy.types.Object.sm64_obj_use_act1
	del bpy.types.Object.sm64_obj_use_act2
	del bpy.types.Object.sm64_obj_use_act3
	del bpy.types.Object.sm64_obj_use_act4
	del bpy.types.Object.sm64_obj_use_act5
	del bpy.types.Object.sm64_obj_use_act6

	del bpy.types.Object.sm64_obj_set_bparam
	del bpy.types.Object.sm64_obj_set_yaw

	del bpy.types.Object.useBackgroundColor
	#del bpy.types.Object.backgroundID
	del bpy.types.Object.background
	del bpy.types.Object.backgroundColor
	
	del bpy.types.Object.screenPos
	del bpy.types.Object.screenSize
	del bpy.types.Object.useDefaultScreenRect
	del bpy.types.Object.clipPlanes
	del bpy.types.Object.area_fog_color
	del bpy.types.Object.area_fog_position
	del bpy.types.Object.areaOverrideBG
	del bpy.types.Object.areaBGColor
	del bpy.types.Object.camOption
	del bpy.types.Object.camType
	del bpy.types.Object.envOption
	del bpy.types.Object.envType
	del bpy.types.Object.fov
	del bpy.types.Object.dynamicFOV

	del bpy.types.Object.cameraVolumeFunction
	del bpy.types.Object.cameraVolumeGlobal

	del bpy.types.Object.starGetCutscenes

	del bpy.types.Object.acousticReach
	del bpy.types.Object.echoLevel
	del bpy.types.Object.zoomOutOnPause

	del bpy.types.Object.areaIndex
	del bpy.types.Object.music_preset
	del bpy.types.Object.music_seq
	del bpy.types.Object.terrain_type
	del bpy.types.Object.areaCamera
	del bpy.types.Object.noMusic

	del bpy.types.Object.showStartDialog
	del bpy.types.Object.startDialog
	del bpy.types.Object.actSelectorIgnore
	del bpy.types.Object.setAsStartLevel
	del bpy.types.Object.switchFunc
	del bpy.types.Object.switchParam 
	del bpy.types.Object.enableRoomSwitch

	for cls in reversed(sm64_obj_classes):
		unregister_class(cls)

'''
object: model, bparam, behaviour, acts
macro: preset, [bparam]
special: preset, [yaw, [bparam]]
trajectory: id
'''