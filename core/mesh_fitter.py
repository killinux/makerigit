# -*- coding: utf-8 -*-

from ..constants import BONE_WEIGHT_ALIASES


def fit_rigid_to_mesh(rigid_obj, arm, mesh, bone_name, shape,
                      pad=1.10, percentile=0.90, weight_threshold=0.3):
    if mesh is None or bone_name not in arm.data.bones:
        return None

    alias_names = BONE_WEIGHT_ALIASES.get(bone_name, [bone_name])
    alias_vg_indices = []
    for n in alias_names:
        vg = mesh.vertex_groups.get(n)
        if vg is not None:
            alias_vg_indices.append(vg.index)
    if not alias_vg_indices:
        return None
    alias_set = set(alias_vg_indices)

    bone = arm.data.bones[bone_name]
    bone_world_mat = arm.matrix_world @ bone.matrix_local
    bone_world_inv = bone_world_mat.inverted()
    mesh_world = mesh.matrix_world

    candidates = []
    for v in mesh.data.vertices:
        w = 0.0
        for g in v.groups:
            if g.group in alias_set:
                w += g.weight
                if w >= weight_threshold:
                    break
        if w < weight_threshold:
            continue
        local = bone_world_inv @ (mesh_world @ v.co)
        candidates.append(local.x * local.x + local.z * local.z)

    if len(candidates) < 10:
        return None
    candidates.sort()
    idx = min(int(len(candidates) * percentile), len(candidates) - 1)
    measured_r = (candidates[idx] ** 0.5) * pad

    old_size = list(rigid_obj.mmd_rigid.size)
    template_r = old_size[0]
    new_r = min(template_r, measured_r)

    if shape == 'SPHERE':
        rigid_obj.mmd_rigid.size = (new_r, 0.0, 0.0)
    elif shape == 'CAPSULE':
        rigid_obj.mmd_rigid.size = (new_r, old_size[1], 0.0)
    else:
        return None
    return old_size, list(rigid_obj.mmd_rigid.size), len(candidates)
