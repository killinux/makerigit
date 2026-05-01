# -*- coding: utf-8 -*-

import bpy
from mathutils import Vector


def find_mmd_root(obj):
    cur = obj
    while cur is not None:
        if getattr(cur, 'mmd_type', '') == 'ROOT':
            return cur
        cur = cur.parent
    if obj is not None:
        for c in obj.children_recursive:
            if getattr(c, 'mmd_type', '') == 'ROOT':
                return c
    return None


def get_mmd_model(root_obj):
    from mmd_tools.core.model import Model as MMDModel
    return MMDModel(root_obj)


def bone_world_midpoint(arm, bone):
    mw = arm.matrix_world
    head = mw @ bone.head_local
    tail = mw @ bone.tail_local
    return (head + tail) * 0.5


def bone_world_rotation_yxz(arm, bone):
    world_mat = arm.matrix_world @ bone.matrix_local
    return world_mat.to_euler('YXZ')


def bone_world_rest_matrix(arm, bone_name):
    return arm.matrix_world @ arm.data.bones[bone_name].matrix_local


def is_internal_helper_bone(name):
    return name.startswith('_dummy_') or name.startswith('_shadow_')


def find_body_mesh(mmd_root):
    body_bones = ('上半身', '上半身2', '下半身', '腕.L', '腕.R',
                  'ひじ.L', 'ひじ.R', '足.L', '足.R', 'ひざ.L', 'ひざ.R',
                  '頭', '首')
    best = None
    best_score = (-1, -1)
    for c in mmd_root.children_recursive:
        if c.type != 'MESH' or getattr(c, 'mmd_type', '') == 'RIGID_BODY':
            continue
        bones_covered = 0
        weighted = 0
        for bname in body_bones:
            vg = c.vertex_groups.get(bname)
            if vg is None:
                continue
            nv = 0
            for v in c.data.vertices:
                for g in v.groups:
                    if g.group == vg.index and g.weight > 0.3:
                        nv += 1
                        break
            if nv > 20:
                bones_covered += 1
                weighted += nv
                break
        score = (bones_covered, weighted)
        if score > best_score:
            best_score = score
            best = c
    return best


def find_best_mesh_for_bone(mmd_root, bone_name):
    from .constants import BONE_WEIGHT_ALIASES
    alias_names = BONE_WEIGHT_ALIASES.get(bone_name, [bone_name])
    best = None
    best_n = 0
    strand_bones = ('上半身', '上半身2', '下半身', '腕.L', '腕.R',
                    '足.L', '足.R', '頭', '首')
    for c in mmd_root.children_recursive:
        if c.type != 'MESH' or getattr(c, 'mmd_type', '') == 'RIGID_BODY':
            continue
        n = 0
        for an in alias_names:
            vg = c.vertex_groups.get(an)
            if vg is None:
                continue
            for v in c.data.vertices:
                for g in v.groups:
                    if g.group == vg.index and g.weight > 0.3:
                        n += 1
                        break
        if n <= best_n:
            continue
        covered = 0
        for bname in strand_bones:
            vg = c.vertex_groups.get(bname)
            if vg is None:
                continue
            cnt = 0
            for v in c.data.vertices:
                for g in v.groups:
                    if g.group == vg.index and g.weight > 0.3:
                        cnt += 1
                        if cnt >= 20:
                            break
                if cnt >= 20:
                    break
            if cnt >= 20:
                covered += 1
        if covered < 2:
            continue
        best_n = n
        best = c
    return best if best_n >= 20 else find_body_mesh(mmd_root)


def get_existing_rigids_by_bone(model):
    result = {}
    for obj in model.rigidBodies():
        bname = obj.mmd_rigid.bone
        if bname:
            result[bname] = obj
    return result
