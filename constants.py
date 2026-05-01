# -*- coding: utf-8 -*-

CANONICAL_BODY_BONES = frozenset([
    '全ての親', '操作中心', 'センター', 'グルーブ', '腰',
    '上半身', '上半身1', '上半身2', '上半身3',
    '下半身',
    '首', '首1', '頭', '両目', '目.L', '目.R',
    '肩.L', '肩.R', '肩C.L', '肩C.R', '肩P.L', '肩P.R',
    '腕.L', '腕.R', 'ひじ.L', 'ひじ.R', '手首.L', '手首.R',
    'ダミー.L', 'ダミー.R',
    '腕捩.L', '腕捩.R', '手捩.L', '手捩.R',
    '腕捩1.L', '腕捩1.R', '腕捩2.L', '腕捩2.R', '腕捩3.L', '腕捩3.R',
    '手捩1.L', '手捩1.R', '手捩2.L', '手捩2.R', '手捩3.L', '手捩3.R',
    '足.L', '足.R', 'ひざ.L', 'ひざ.R', '足首.L', '足首.R',
    '足D.L', '足D.R', 'ひざD.L', 'ひざD.R', '足首D.L', '足首D.R',
    '足先EX.L', '足先EX.R',
    '足IK.L', '足IK.R', 'つま先IK.L', 'つま先IK.R',
    '足ＩＫ.L', '足ＩＫ.R', 'つま先ＩＫ.L', 'つま先ＩＫ.R',
    '足IK親.L', '足IK親.R', '足ＩＫ親.L', '足ＩＫ親.R',
    'つま先.L', 'つま先.R',
    '腰キャンセル.L', '腰キャンセル.R',
])

_FINGER_ROOTS = ('親指', '人指', '中指', '薬指', '小指')
for _root in _FINGER_ROOTS:
    for _i in '0123':
        for _side in ('.L', '.R'):
            CANONICAL_BODY_BONES = CANONICAL_BODY_BONES | {f'{_root}{_i}{_side}'}
    for _i in '０１２３':
        for _side in ('.L', '.R'):
            CANONICAL_BODY_BONES = CANONICAL_BODY_BONES | {f'{_root}{_i}{_side}'}

ANCHOR_BONE_MAP = {
    'HAIR':      frozenset(['頭']),
    'SKIRT':     frozenset(['下半身']),
    'SLEEVE_L':  frozenset(['手首.L']),
    'SLEEVE_R':  frozenset(['手首.R']),
    'BREAST':    frozenset(['上半身2', '上半身', '上半身3']),
    'TAIL':      frozenset(['下半身', '尻']),
}

REGION_DEFAULT_COLLISION_GROUP = {
    'HAIR': 2,
    'SKIRT': 3,
    'SLEEVE_L': 4,
    'SLEEVE_R': 4,
    'BREAST': 15,
    'TAIL': 5,
    'OTHER': 6,
}

BREAST_BONE_PATTERNS = ('乳奶', '胸', 'おっぱい', 'breast')

BREAST_ANCHOR_PRIORITY = ['上半身2', '上半身', '上半身3']

SHAPE_IDX = {'SPHERE': 0, 'BOX': 1, 'CAPSULE': 2}

BONE_WEIGHT_ALIASES = {
    '足.L':   ['足.L', '足D.L'],
    '足.R':   ['足.R', '足D.R'],
    'ひざ.L': ['ひざ.L', 'ひざD.L'],
    'ひざ.R': ['ひざ.R', 'ひざD.R'],
    '足首.L': ['足首.L', '足首D.L'],
    '足首.R': ['足首.R', '足首D.R'],
    '腕.L':   ['腕.L', '腕捩.L', '腕捩1.L', '腕捩2.L', '腕捩3.L'],
    '腕.R':   ['腕.R', '腕捩.R', '腕捩1.R', '腕捩2.R', '腕捩3.R'],
    'ひじ.L': ['ひじ.L', '手捩.L', '手捩1.L', '手捩2.L', '手捩3.L'],
    'ひじ.R': ['ひじ.R', '手捩.R', '手捩1.R', '手捩2.R', '手捩3.R'],
}

BREAST_PRESETS = {
    'SUBTLE': {
        'mass': 0.8, 'friction': 0.5,
        'linear_damping': 0.8, 'angular_damping': 0.8,
        'bounce': 0.1,
        'limit_x': 8.0, 'limit_y': 5.0, 'limit_z': 8.0,
        'spring_ang_x': 100.0, 'spring_ang_y': 100.0, 'spring_ang_z': 100.0,
        'spring_lin_x': 0.0, 'spring_lin_y': 0.0, 'spring_lin_z': 0.0,
    },
    'NATURAL': {
        'mass': 1.0, 'friction': 0.5,
        'linear_damping': 0.5, 'angular_damping': 0.5,
        'bounce': 0.3,
        'limit_x': 15.0, 'limit_y': 10.0, 'limit_z': 15.0,
        'spring_ang_x': 50.0, 'spring_ang_y': 50.0, 'spring_ang_z': 50.0,
        'spring_lin_x': 0.0, 'spring_lin_y': 0.0, 'spring_lin_z': 0.0,
    },
    'BOUNCY': {
        'mass': 1.2, 'friction': 0.5,
        'linear_damping': 0.3, 'angular_damping': 0.3,
        'bounce': 0.6,
        'limit_x': 25.0, 'limit_y': 15.0, 'limit_z': 25.0,
        'spring_ang_x': 20.0, 'spring_ang_y': 20.0, 'spring_ang_z': 20.0,
        'spring_lin_x': 0.0, 'spring_lin_y': 0.0, 'spring_lin_z': 0.0,
    },
    'DRAMATIC': {
        'mass': 1.5, 'friction': 0.5,
        'linear_damping': 0.2, 'angular_damping': 0.2,
        'bounce': 0.8,
        'limit_x': 35.0, 'limit_y': 20.0, 'limit_z': 35.0,
        'spring_ang_x': 10.0, 'spring_ang_y': 10.0, 'spring_ang_z': 10.0,
        'spring_lin_x': 0.0, 'spring_lin_y': 0.0, 'spring_lin_z': 0.0,
    },
}
