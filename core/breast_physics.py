# -*- coding: utf-8 -*-

import math
from ..constants import (
    SHAPE_IDX, BREAST_BONE_PATTERNS, BREAST_ANCHOR_PRIORITY,
    BREAST_PRESETS,
)
from ..utils import (
    bone_world_midpoint, bone_world_rotation_yxz,
    find_body_mesh, find_best_mesh_for_bone, get_existing_rigids_by_bone,
)
from .mesh_fitter import fit_rigid_to_mesh


def find_breast_bones(arm):
    results = []
    for bone in arm.data.bones:
        for pat in BREAST_BONE_PATTERNS:
            if pat in bone.name:
                results.append(bone)
                break
    return results


def find_anchor_bone(arm):
    for name in BREAST_ANCHOR_PRIORITY:
        if name in arm.data.bones:
            return arm.data.bones[name]
    return None


def get_breast_params(preset_name=None, **overrides):
    if preset_name and preset_name in BREAST_PRESETS:
        params = dict(BREAST_PRESETS[preset_name])
    else:
        params = dict(BREAST_PRESETS['NATURAL'])
    params.update(overrides)
    return params


def create_breast_physics(model, arm, mmd_root, *,
                          preset_name='NATURAL',
                          shape='SPHERE',
                          auto_fit_size=True,
                          size_multiplier=1.0,
                          fit_pad=1.10,
                          collision_group=15,
                          collision_mask=None,
                          **param_overrides):
    from mmd_tools.core.rigid_body import MODE_STATIC, MODE_DYNAMIC

    params = get_breast_params(preset_name, **param_overrides)

    breast_bones = find_breast_bones(arm)
    if not breast_bones:
        return 0, 0, ['No breast bones found']

    anchor_bone = find_anchor_bone(arm)
    if anchor_bone is None:
        return 0, 0, ['No anchor bone found (上半身2/上半身)']

    existing = get_existing_rigids_by_bone(model)

    if collision_mask is None:
        collision_mask = [True] * 16

    anchor_rigid = existing.get(anchor_bone.name)
    anchor_created = False
    if anchor_rigid is None:
        anchor_loc = bone_world_midpoint(arm, anchor_bone)
        anchor_rot = bone_world_rotation_yxz(arm, anchor_bone)
        anchor_size = (max(anchor_bone.length * 0.3, 0.02), anchor_bone.length, 0.0)
        anchor_rigid = model.createRigidBody(
            shape_type=SHAPE_IDX['CAPSULE'],
            location=anchor_loc,
            rotation=anchor_rot,
            size=anchor_size,
            dynamics_type=MODE_STATIC,
            name=anchor_bone.name,
            name_e=anchor_bone.name,
            bone=anchor_bone.name,
            friction=0.5,
            mass=1.0,
            angular_damping=0.999,
            linear_damping=0.999,
            bounce=0.0,
            collision_group_number=0,
            collision_group_mask=[False] * 16,
        )
        anchor_created = True

    n_rigids = 1 if anchor_created else 0
    n_joints = 0
    skipped = []
    bone_to_rigid = {anchor_bone.name: anchor_rigid}

    for breast_bone in breast_bones:
        if breast_bone.name in existing:
            bone_to_rigid[breast_bone.name] = existing[breast_bone.name]
            skipped.append(f'{breast_bone.name} (already exists)')
            continue

        loc = bone_world_midpoint(arm, breast_bone)
        rot = bone_world_rotation_yxz(arm, breast_bone)
        bone_length = max(breast_bone.length, 0.01)
        radius = bone_length * size_multiplier

        if shape == 'SPHERE':
            size = (radius, 0.0, 0.0)
        else:
            size = (radius, bone_length, 0.0)

        rigid = model.createRigidBody(
            shape_type=SHAPE_IDX[shape],
            location=loc,
            rotation=rot,
            size=size,
            dynamics_type=MODE_DYNAMIC,
            name=breast_bone.name,
            name_e=breast_bone.name,
            bone=breast_bone.name,
            friction=params['friction'],
            mass=params['mass'],
            angular_damping=params['angular_damping'],
            linear_damping=params['linear_damping'],
            bounce=params['bounce'],
            collision_group_number=collision_group,
            collision_group_mask=collision_mask,
        )
        bone_to_rigid[breast_bone.name] = rigid
        n_rigids += 1

        if auto_fit_size:
            mesh = find_best_mesh_for_bone(mmd_root, breast_bone.name)
            if mesh is None:
                mesh = find_body_mesh(mmd_root)
            if mesh is not None:
                fit_rigid_to_mesh(rigid, arm, mesh, breast_bone.name, shape,
                                  pad=fit_pad)

    for breast_bone in breast_bones:
        rigid_b = bone_to_rigid.get(breast_bone.name)
        if rigid_b is None:
            continue

        parent = breast_bone.parent
        if parent is None:
            continue
        rigid_a = bone_to_rigid.get(parent.name)
        if rigid_a is None:
            rigid_a = anchor_rigid

        lx = math.radians(params['limit_x'])
        ly = math.radians(params['limit_y'])
        lz = math.radians(params['limit_z'])

        joint_loc = arm.matrix_world @ breast_bone.head_local
        joint_rot = bone_world_rotation_yxz(arm, breast_bone)

        model.createJoint(
            name=breast_bone.name,
            name_e=breast_bone.name,
            location=joint_loc,
            rotation=joint_rot,
            rigid_a=rigid_a,
            rigid_b=rigid_b,
            maximum_location=(0.0, 0.0, 0.0),
            minimum_location=(0.0, 0.0, 0.0),
            maximum_rotation=(lx, ly, lz),
            minimum_rotation=(-lx, -ly, -lz),
            spring_angular=(params['spring_ang_x'], params['spring_ang_y'],
                            params['spring_ang_z']),
            spring_linear=(params['spring_lin_x'], params['spring_lin_y'],
                           params['spring_lin_z']),
        )
        n_joints += 1

    return n_rigids, n_joints, skipped
