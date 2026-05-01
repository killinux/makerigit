# -*- coding: utf-8 -*-

import math
from ..constants import SHAPE_IDX, REGION_DEFAULT_COLLISION_GROUP
from ..utils import bone_world_midpoint, bone_world_rotation_yxz


def create_rigid_for_bone(model, arm, bone, *,
                          is_root=False,
                          depth=0,
                          shape_override=None,
                          radius_ratio=0.15,
                          base_mass=0.5,
                          mass_decay=0.8,
                          friction=0.5,
                          linear_damping=0.5,
                          angular_damping=0.5,
                          bounce=0.0,
                          collision_group=2,
                          collision_mask=None):
    from mmd_tools.core.rigid_body import MODE_STATIC, MODE_DYNAMIC

    bone_length = max(bone.length, 0.01)
    radius = max(bone_length * radius_ratio, 0.005)
    has_children = len(bone.children) > 0

    if shape_override:
        shape = shape_override
    elif has_children:
        shape = 'CAPSULE'
    else:
        shape = 'SPHERE'

    if shape == 'CAPSULE':
        size = (radius, bone_length, 0.0)
    elif shape == 'SPHERE':
        size = (radius, 0.0, 0.0)
    else:
        size = (radius, radius, bone_length * 0.8)

    loc = bone_world_midpoint(arm, bone)
    rot = bone_world_rotation_yxz(arm, bone)
    mass = base_mass * (mass_decay ** depth)
    dynamics_type = MODE_STATIC if is_root else MODE_DYNAMIC

    if collision_mask is None:
        collision_mask = [False] * 16
        collision_mask[0] = True
        if collision_group > 0:
            collision_mask[collision_group - 1] = True

    return model.createRigidBody(
        shape_type=SHAPE_IDX[shape],
        location=loc,
        rotation=rot,
        size=size,
        dynamics_type=dynamics_type,
        name=bone.name,
        name_e=bone.name,
        bone=bone.name,
        friction=friction,
        mass=mass,
        angular_damping=angular_damping,
        linear_damping=linear_damping,
        bounce=bounce,
        collision_group_number=collision_group,
        collision_group_mask=collision_mask,
    )


def create_rigids_for_chain(model, arm, chain_info, *,
                            skip_existing=None,
                            radius_ratio=0.15,
                            base_mass=0.5,
                            mass_decay=0.8,
                            friction=0.5,
                            linear_damping=0.5,
                            angular_damping=0.5,
                            bounce=0.0,
                            collision_group=2,
                            collision_mask=None):
    if skip_existing is None:
        skip_existing = {}

    bone_to_rigid = {}
    created = 0

    for bone in chain_info['chain']:
        if bone.name in skip_existing:
            bone_to_rigid[bone.name] = skip_existing[bone.name]
            continue

        depth = chain_info['depth_by_name'].get(bone.name, 0)
        is_root = (bone == chain_info['root'])

        rigid = create_rigid_for_bone(
            model, arm, bone,
            is_root=is_root,
            depth=depth,
            radius_ratio=radius_ratio,
            base_mass=base_mass,
            mass_decay=mass_decay,
            friction=friction,
            linear_damping=linear_damping,
            angular_damping=angular_damping,
            bounce=bounce,
            collision_group=collision_group,
            collision_mask=collision_mask,
        )
        bone_to_rigid[bone.name] = rigid
        created += 1

    return bone_to_rigid, created
