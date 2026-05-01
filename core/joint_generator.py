# -*- coding: utf-8 -*-

import math
from ..utils import bone_world_rotation_yxz


def create_joint_for_pair(model, arm, rigid_a, rigid_b, child_bone, *,
                          depth=0,
                          max_depth=1,
                          root_angle_deg=10.0,
                          leaf_angle_deg=30.0,
                          max_rotation_override=None,
                          min_rotation_override=None,
                          spring_angular=(0.0, 0.0, 0.0),
                          spring_linear=(0.0, 0.0, 0.0)):
    loc = arm.matrix_world @ child_bone.head_local
    rot = bone_world_rotation_yxz(arm, child_bone)

    if max_rotation_override is not None and min_rotation_override is not None:
        max_rot = max_rotation_override
        min_rot = min_rotation_override
    else:
        t = depth / max_depth if max_depth > 0 else 1.0
        ang_deg = root_angle_deg + (leaf_angle_deg - root_angle_deg) * t
        ang_rad = math.radians(ang_deg)
        max_rot = (ang_rad, ang_rad, ang_rad)
        min_rot = (-ang_rad, -ang_rad, -ang_rad)

    return model.createJoint(
        name=child_bone.name,
        name_e=child_bone.name,
        location=loc,
        rotation=rot,
        rigid_a=rigid_a,
        rigid_b=rigid_b,
        maximum_location=(0.0, 0.0, 0.0),
        minimum_location=(0.0, 0.0, 0.0),
        maximum_rotation=max_rot,
        minimum_rotation=min_rot,
        spring_angular=spring_angular,
        spring_linear=spring_linear,
    )


def create_joints_for_chain(model, arm, chain_info, bone_to_rigid, *,
                            root_angle_deg=10.0,
                            leaf_angle_deg=30.0,
                            spring_angular=(0.0, 0.0, 0.0),
                            spring_linear=(0.0, 0.0, 0.0)):
    max_depth = chain_info['max_depth']
    created = 0

    for bone in chain_info['chain']:
        parent = bone.parent
        if parent is None:
            continue
        rigid_a = bone_to_rigid.get(parent.name)
        rigid_b = bone_to_rigid.get(bone.name)
        if rigid_a is None or rigid_b is None:
            continue

        depth = chain_info['depth_by_name'].get(bone.name, 0)

        create_joint_for_pair(
            model, arm, rigid_a, rigid_b, bone,
            depth=depth,
            max_depth=max_depth,
            root_angle_deg=root_angle_deg,
            leaf_angle_deg=leaf_angle_deg,
            spring_angular=spring_angular,
            spring_linear=spring_linear,
        )
        created += 1

    return created
