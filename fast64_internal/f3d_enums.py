
combiner_enums = {
	'Case A' : (
	('COMBINED', 'Combined Color', 'Combined Color'),
	('TEXEL0', 'Texture 0', 'Texture 0'),
	('TEXEL1', 'Texture 1', 'Texture 1'),
	('PRIMITIVE', 'Primitive Color', 'Primitive Color'),
	('SHADE', 'Shade Color', 'Shade Color'),
	('ENVIRONMENT', 'Environment Color', 'Environment Color'),
	('1', '1', '1'),
	('NOISE', 'Noise', 'Noise'),
	('0', '0', '0'),
	),
	
	'Case B' : (
	('COMBINED', 'Combined Color', 'Combined Color'),
	('TEXEL0', 'Texture 0', 'Texture 0'),
	('TEXEL1', 'Texture 1', 'Texture 1'),
	('PRIMITIVE', 'Primitive Color', 'Primitive Color'),
	('SHADE', 'Shade Color', 'Shade Color'),
	('ENVIRONMENT', 'Environment Color', 'Environment Color'),
	('CENTER', 'Chroma Key Center', 'Chroma Key Center'),
	('K4', 'YUV Convert K4', 'YUV Convert K4'),
	('0', '0', '0')
	),
	
	'Case C' : (
	('COMBINED'  , 'Combined Color', 'Combined Color'),
	('TEXEL0'  , 'Texture 0', 'Texture 0'),
	('TEXEL1'  , 'Texture 1', 'Texture 1'),
	('PRIMITIVE'  , 'Primitive Color', 'Primitive Color'),
	('SHADE'  , 'Shade Color', 'Shade Color'),
	('ENVIRONMENT'  , 'Environment Color', 'Environment Color'),
	('SCALE'  , 'Chroma Key Scale', 'Chroma Key Scale'),
	('COMBINED_ALPHA'  , 'Combined Color Alpha', 'Combined Color Alpha'),
	('TEXEL0_ALPHA'  , 'Texture 0 Alpha', 'Texture 0 Alpha'),
	('TEXEL1_ALPHA'  , 'Texture 1 Alpha', 'Texture 1 Alpha'),
	('PRIMITIVE_ALPHA' , 'Primitive Color Alpha', 'Primitive Color Alpha'),
	('SHADE_ALPHA' , 'Shade Color Alpha', 'Shade Color Alpha'),
	('ENV_ALPHA' , 'Environment Color Alpha', 'Environment Color Alpha'),
	('LOD_FRACTION' , 'LOD Fraction', 'LOD Fraction'),
	('PRIM_LOD_FRAC' , 'Primitive LOD Fraction', 'Primitive LOD Fraction'),
	('K5' , 'YUV Convert K5', 'YUV Convert K5'),
	('0' , '0', '0'),
	),
	
	'Case D' : (
	('COMBINED', 'Combined Color', 'Combined Color'),
	('TEXEL0', 'Texture 0', 'Texture 0'),
	('TEXEL1', 'Texture 1', 'Texture 1'),
	('PRIMITIVE', 'Primitive Color', 'Primitive Color'),
	('SHADE', 'Shade Color', 'Shade Color'),
	('ENVIRONMENT', 'Environment Color', 'Environment Color'),
	('1', '1', '1'),
	('0', '0', '0'),
	),
	
	'Case A Alpha' : (
	('COMBINED', 'Combined Color Alpha', 'Combined Color Alpha'),
	('TEXEL0', 'Texture 0 Alpha', 'Texture 0 Alpha'),
	('TEXEL1', 'Texture 1 Alpha', 'Texture 1 Alpha'),
	('PRIMITIVE', 'Primitive Color Alpha', 'Primitive Color Alpha'),
	('SHADE', 'Shade Color Alpha', 'Shade Color Alpha'),
	('ENVIRONMENT', 'Environment Color Alpha', 'Environment Color Alpha'),
	('1', '1', '1'),
	('0', '0', '0'),
	),
	
	'Case B Alpha' : (
	('COMBINED', 'Combined Color Alpha', 'Combined Color Alpha'),
	('TEXEL0', 'Texture 0 Alpha', 'Texture 0 Alpha'),
	('TEXEL1', 'Texture 1 Alpha', 'Texture 1 Alpha'),
	('PRIMITIVE', 'Primitive Color Alpha', 'Primitive Color Alpha'),
	('SHADE', 'Shade Color Alpha', 'Shade Color Alpha'),
	('ENVIRONMENT', 'Environment Color Alpha', 'Environment Color Alpha'),
	('1', '1', '1'),
	('0', '0', '0'),
	),
	
	'Case C Alpha' : (
	('LOD_FRACTION', 'LOD Fraction', 'LOD Fraction'),
	('TEXEL0', 'Texture 0 Alpha', 'Texture 0 Alpha'),
	('TEXEL1', 'Texture 1 Alpha', 'Texture 1 Alpha'),
	('PRIMITIVE', 'Primitive Color Alpha', 'Primitive Color Alpha'),
	('SHADE', 'Shade Color Alpha', 'Shade Color Alpha'),
	('ENVIRONMENT', 'Environment Color Alpha', 'Environment Color Alpha'),
	('PRIM_LOD_FRAC', 'Primitive LOD Fraction', 'Primitive LOD Fraction'),
	('0', '0', '0'),
	),
	
	'Case D Alpha' : (
	('COMBINED', 'Combined Color Alpha', 'Combined Color Alpha'),
	('TEXEL0', 'Texture 0 Alpha', 'Texture 0 Alpha'),
	('TEXEL1', 'Texture 1 Alpha', 'Texture 1 Alpha'),
	('PRIMITIVE', 'Primitive Color Alpha', 'Primitive Color Alpha'),
	('SHADE', 'Shade Color Alpha', 'Shade Color Alpha'),
	('ENVIRONMENT', 'Environment Color Alpha', 'Environment Color Alpha'),
	('1', '1', '1'),
	('0', '0', '0'),
	),
}

caseTemplateDict = {
	'Case A' : 'Fast3D_A',
	'Case B' : 'Fast3D_B',
	'Case C' : 'Fast3D_C',
	'Case D' : 'Fast3D_D',
	'Case A Alpha' : 'Fast3D_A_alpha',
	'Case B Alpha' : 'Fast3D_B_alpha',
	'Case C Alpha' : 'Fast3D_C_alpha',
	'Case D Alpha' : 'Fast3D_D_alpha',
}

caseTemplateDict2 = {
	'Case A' : 'ShaderNodeValue',
	'Case B' : 'ShaderNodeValue',
	'Case C' : 'ShaderNodeValue',
	'Case D' : 'ShaderNodeValue',
	'Case A Alpha' : 'ShaderNodeValue',
	'Case B Alpha' : 'ShaderNodeValue',
	'Case C Alpha' : 'ShaderNodeValue',
	'Case D Alpha' : 'ShaderNodeValue',
}

# hardware v2
enumAlphaDither = [
	('G_AD_PATTERN', 'Pattern', 'Pattern'),
	('G_AD_NOTPATTERN', 'NOT Pattern', 'NOT Pattern'),
	('G_AD_NOISE', 'Noise', 'Noise'),
	('G_AD_DISABLE', 'Disable', 'Disable'),
]

# hardware v2
enumRGBDither = [
	('G_CD_MAGICSQ', 'Magic Square', 'Magic Square'),
	('G_CD_BAYER', 'Bayer', 'Bayer'),
	('G_CD_NOISE', 'Noise', 'Noise'),
	('G_CD_DISABLE', 'Disable', 'Disable'),
	('G_CD_ENABLE', 'Enable', 'Enable')
]

enumCombKey = [
	('G_CK_NONE', 'None', 'None'),
	('G_CK_KEY', 'Key', 'Key'),
]

enumTextConv = [
	('G_TC_CONV', 'Convert', 'Convert'),
	('G_TC_FILTCONV', 'Filter And Convert', 'Filter And Convert'),
	('G_TC_FILT', 'Filter', 'Filter')
]

enumTextFilt = [
	('G_TF_POINT', 'Point', 'Point'),
	('G_TF_AVERAGE', 'Average', 'Average'),
	('G_TF_BILERP', 'Bilinear', 'Bilinear'),
]

enumTextLUT = [
	('G_TT_NONE', 'None', 'None'),
	('G_TT_RGBA16', 'RGBA16', 'RGBA16'),
	('G_TT_IA16', 'IA16', 'IA16'),
]

enumTextLOD = [
	('G_TL_TILE', 'Tile', 'Tile'),
	('G_TL_LOD', 'LOD', 'LOD'),
]

enumTextDetail = [
	('G_TD_CLAMP', 'Clamp', 'Clamp'),
	('G_TD_SHARPEN', 'Sharpen', 'Sharpen'),
	('G_TD_DETAIL', 'Detail', 'Detail'),
]

enumTextPersp = [
	('G_TP_NONE', 'None', 'None'),
	('G_TP_PERSP', 'Perspective', 'Perspective'),
]

enumCycleType = [
	('G_CYC_1CYCLE', '1 Cycle', '1 Cycle'),
	('G_CYC_2CYCLE', '2 Cycle', '2 Cycle'),
	('G_CYC_COPY', 'Copy', 'Copy'),
	('G_CYC_FILL', 'Fill', 'Fill'),
]

enumColorDither = [
	('G_CD_DISABLE', 'Disable', 'Disable'),
	('G_CD_ENABLE', 'Enable', 'Enable')
]

enumPipelineMode = [
	('G_PM_1PRIMITIVE', '1 Primitive', '1 Primitive'),
	('G_PM_NPRIMITIVE', 'N Primitive', 'N Primitive')	
]

enumAlphaCompare = [
	('G_AC_NONE', 'None', 'None'),
	('G_AC_THRESHOLD', 'Threshold', 'Threshold'),
	('G_AC_DITHER', 'Dither', 'Dither'),
]

enumDepthSource = [
	('G_ZS_PIXEL', 'Pixel', 'Pixel'),
	('G_ZS_PRIM', 'Primitive', 'Primitive'),
]

enumCoverage = [
	('CVG_DST_CLAMP', 'Clamp', 'Clamp'),
	('CVG_DST_WRAP', 'Wrap', 'Wrap'),
	('CVG_DST_FULL', 'Full', 'Full'),
	('CVG_DST_SAVE', 'Save', 'Save')
]

enumZMode = [
	('ZMODE_OPA', 'Opaque', 'Opaque'),
	('ZMODE_INTER', 'Interpenetrating', 'Interpenetrating'),
	('ZMODE_XLU', 'Transparent (XLU)', 'Transparent (XLU)'),
	('ZMODE_DEC', 'Decal', 'Decal')
]

enumBlendColor = [
	('G_BL_CLR_IN', 'Input', 'Input'),
	('G_BL_CLR_MEM', 'Memory', 'Memory'),
	('G_BL_CLR_BL', 'Blend', 'Blend'),
	('G_BL_CLR_FOG', 'Fog', 'Fog')
]

enumBlendAlpha = [
	('G_BL_A_IN', 'Input', 'Input'),
	('G_BL_A_FOG', 'Fog', 'Fog'),
	('G_BL_A_SHADE', 'Shade', 'Shade'),
	('G_BL_0', '0', '0')
]

enumBlendMix = [
	('G_BL_1MA', '1 - Source Alpha', '1 - Source Alpha'),
	('G_BL_A_MEM', 'Memory Alpha', 'Memory Alpha'),
	('G_BL_1', '1', '1'),
	('G_BL_0', '0', '0')
]

enumRenderModesCycle1 = [
	#('Use Draw Layer', 'Use Draw Layer', 'Use Draw Layer'),
	('G_RM_ZB_OPA_SURF', 'Background', 'G_RM_ZB_OPA_SURF'),
    ('G_RM_AA_ZB_OPA_SURF', 'Opaque', 'G_RM_AA_ZB_OPA_SURF'),
    ('G_RM_AA_ZB_OPA_DECAL', 'Opaque Decal', 'G_RM_AA_ZB_OPA_DECAL'),
    ('G_RM_AA_ZB_OPA_INTER', 'Opaque Intersecting', 'G_RM_AA_ZB_OPA_INTER'),
    ('G_RM_AA_ZB_TEX_EDGE', 'Cutout', 'G_RM_AA_ZB_TEX_EDGE'),
    ('G_RM_AA_ZB_XLU_SURF', 'Transparent', 'G_RM_AA_ZB_XLU_SURF'),
    ('G_RM_AA_ZB_XLU_DECAL', 'Transparent Decal', 'G_RM_AA_ZB_XLU_DECAL'),
    ('G_RM_AA_ZB_XLU_INTER', 'Transparent Intersecting', 'G_RM_AA_ZB_XLU_INTER'),
	('G_RM_FOG_SHADE_A', 'Fog Shade', 'G_RM_FOG_SHADE_A'),
	('G_RM_FOG_PRIM_A', 'Fog Primitive', 'G_RM_FOG_PRIM_A'),
	('G_RM_PASS', 'Pass', 'G_RM_PASS'),
	('G_RM_ADD', 'Add', 'G_RM_ADD'),
	('G_RM_NOOP', 'No Op', 'G_RM_NOOP'),
]

enumRenderModesCycle2 = [
	#('Use Draw Layer', 'Use Draw Layer', 'Use Draw Layer'),
	('G_RM_ZB_OPA_SURF2', 'Background', 'G_RM_ZB_OPA_SURF2'),
    ('G_RM_AA_ZB_OPA_SURF2', 'Opaque', 'G_RM_AA_ZB_OPA_SURF2'),
    ('G_RM_AA_ZB_OPA_DECAL2', 'Opaque Decal', 'G_RM_AA_ZB_OPA_DECAL2'),
    ('G_RM_AA_ZB_OPA_INTER2', 'Opaque Intersecting', 'G_RM_AA_ZB_OPA_INTER2'),
    ('G_RM_AA_ZB_TEX_EDGE2', 'Cutout', 'G_RM_AA_ZB_TEX_EDGE2'),
    ('G_RM_AA_ZB_XLU_SURF2', 'Transparent', 'G_RM_AA_ZB_XLU_SURF2'),
    ('G_RM_AA_ZB_XLU_DECAL2', 'Transparent Decal', 'G_RM_AA_ZB_XLU_DECAL2'),
    ('G_RM_AA_ZB_XLU_INTER2', 'Transparent Intersecting', 'G_RM_AA_ZB_XLU_INTER2'),
	('G_RM_ADD2', 'Add', 'G_RM_ADD2'),
	('G_RM_NOOP', 'No Op', 'G_RM_NOOP'),
]

enumTexFormat = [
	('I4','Intensity 4-bit', 'Intensity 4-bit'),
	('I8','Intensity 8-bit', 'Intensity 8-bit'),
	('IA4','Intensity Alpha 4-bit', 'Intensity Alpha 4-bit'),
	('IA8','Intensity Alpha 8-bit', 'Intensity Alpha 8-bit'),
	('IA16','Intensity Alpha 16-bit', 'Intensity Alpha 16-bit'),
	('CI4','Color Index 4-bit', 'Color Index 4-bit'),
	('CI8','Color Index 8-bit', 'Color Index 8-bit'),
	('RGBA16','RGBA 16-bit', 'RGBA 16-bit'),
	('RGBA32','RGBA 32-bit', 'RGBA 32-bit'),
	#('YUV16','YUV 16-bit', 'YUV 16-bit'),
]

enumCIFormat = [
	('RGBA16','RGBA 16-bit', 'RGBA 16-bit'),
	('IA16','Intensity Alpha 16-bit', 'Intensity Alpha 16-bit'),
]

enumTexUV = [
	('TEXEL0', 'Texture 0', 'Texture 0'),
	('TEXEL1', 'Texture 1', 'Texture 1'),
]

texBitSize = {
	'I4' : 4,
	'IA4' : 4,
	'CI4' : 4,
	'I8' : 8,
	'IA8' : 8,
	'CI8' : 8,
	'RGBA16' : 16,
	'IA16' : 16,
	'YUV16' : 16,
	'RGBA32' : 32,
}

# 512 words * 64 bits / n bitSize
maxTexelCount = {
	32 : 1024,
	16 : 2048,
	8 : 4096,
	4 : 8192,
}

enumF3D = [
	#('F3D_GBI', 'Fast3D', "Fast3D"),
	#('F3DEX_GBI', 'F3DEX', "F3DEX"),
	#('F3DEX_GBI_2', 'F3DEX2', "F3DEX2"),
	('F3D', 'F3D', 'F3D'),
	('F3DEX/LX', 'F3DEX/LX', 'F3DEX/LX'),
	('F3DLX.Rej', 'F3DLX.Rej', 'F3DLX.Rej'),
	('F3DLP.Rej', 'F3DLP.Rej', 'F3DLP.Rej'),
	('F3DEX2/LX2', 'F3DEX2/LX2', 'F3DEX2/LX2'),
	('F3DEX2.Rej/LX2.Rej', 'F3DEX2.Rej/LX2.Rej', 'F3DEX2.Rej/LX2.Rej'),
]