# -*- coding: utf-8 -*-

import bpy
from ..utils import find_mmd_root, get_mmd_model, get_existing_rigids_by_bone
from ..utils import find_body_mesh, find_best_mesh_for_bone
from ..constants import REGION_DEFAULT_COLLISION_GROUP


class MAKERIGIT_OT_auto_physics(bpy.types.Operator):
    bl_idname = 'makerigit.auto_physics'
    bl_label = 'Auto Generate All Physics'
    bl_description = 'Detect all dynamic bone chains and generate physics automatically'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        root = find_mmd_root(context.active_object)
        if root is None:
            self.report({'ERROR'}, 'No MMD model found')
            return {'CANCELLED'}

        model = get_mmd_model(root)
        arm = model.armature()
        settings = context.scene.makerigit_settings

        from ..core.chain_detector import detect_all_chains
        from ..core.rigid_generator import create_rigids_for_chain
        from ..core.joint_generator import create_joints_for_chain
        from ..core.breast_physics import create_breast_physics
        from ..core.mesh_fitter import fit_rigid_to_mesh

        existing = get_existing_rigids_by_bone(model)
        regions = detect_all_chains(arm)

        total_rigids = 0
        total_joints = 0

        region_enabled = {
            'HAIR': settings.include_hair,
            'SKIRT': settings.include_skirt,
            'SLEEVE_L': settings.include_sleeve,
            'SLEEVE_R': settings.include_sleeve,
            'TAIL': settings.include_other,
            'OTHER': settings.include_other,
        }

        for region_name, chains in regions.items():
            if region_name == 'BREAST':
                continue
            if not region_enabled.get(region_name, settings.include_other):
                continue

            group = REGION_DEFAULT_COLLISION_GROUP.get(region_name, 6)
            mask = [False] * 16
            mask[0] = True
            if group > 0:
                mask[group - 1] = True

            region_params = _get_region_params(settings, region_name)
            rigid_params = {k: v for k, v in region_params.items()
                           if k not in ('root_angle_deg', 'leaf_angle_deg')}

            for chain_info in chains:
                bone_to_rigid, n_r = create_rigids_for_chain(
                    model, arm, chain_info,
                    skip_existing=existing,
                    collision_group=group,
                    collision_mask=mask,
                    **rigid_params,
                )
                n_j = create_joints_for_chain(
                    model, arm, chain_info, bone_to_rigid,
                    root_angle_deg=region_params.get('root_angle_deg', 10.0),
                    leaf_angle_deg=region_params.get('leaf_angle_deg', 30.0),
                )
                total_rigids += n_r
                total_joints += n_j
                existing.update(bone_to_rigid)

                if settings.fit_to_mesh:
                    fallback_mesh = find_body_mesh(root)
                    if fallback_mesh:
                        for bone in chain_info['chain']:
                            rigid = bone_to_rigid.get(bone.name)
                            if rigid:
                                mesh = find_best_mesh_for_bone(root, bone.name) or fallback_mesh
                                shape = rigid.mmd_rigid.shape
                                fit_rigid_to_mesh(rigid, arm, mesh,
                                                  bone.name, shape)

        if settings.include_breast and 'BREAST' in regions:
            n_r, n_j, skipped = create_breast_physics(
                model, arm, root,
                preset_name=settings.breast_preset,
                shape=settings.breast_shape,
                auto_fit_size=settings.breast_auto_fit,
                size_multiplier=settings.breast_size_mult,
                mass=settings.breast_mass,
                friction=settings.breast_friction,
                linear_damping=settings.breast_linear_damping,
                angular_damping=settings.breast_angular_damping,
                bounce=settings.breast_bounce,
                limit_x=settings.breast_limit_x,
                limit_y=settings.breast_limit_y,
                limit_z=settings.breast_limit_z,
                spring_ang_x=settings.breast_spring_ang_x,
                spring_ang_y=settings.breast_spring_ang_y,
                spring_ang_z=settings.breast_spring_ang_z,
                spring_lin_x=settings.breast_spring_lin_x,
                spring_lin_y=settings.breast_spring_lin_y,
                spring_lin_z=settings.breast_spring_lin_z,
            )
            total_rigids += n_r
            total_joints += n_j

        self.report({'INFO'},
                    f'Created {total_rigids} rigid bodies, {total_joints} joints')
        return {'FINISHED'}


def _get_region_params(settings, region_name):
    if region_name == 'HAIR':
        return {
            'radius_ratio': settings.hair_radius_ratio,
            'base_mass': settings.hair_mass,
            'friction': 0.5,
            'linear_damping': settings.hair_damping,
            'angular_damping': settings.hair_damping,
            'root_angle_deg': settings.hair_root_angle,
            'leaf_angle_deg': settings.hair_leaf_angle,
        }
    elif region_name == 'SKIRT':
        return {
            'radius_ratio': settings.skirt_radius_ratio,
            'base_mass': settings.skirt_mass,
            'friction': 0.5,
            'linear_damping': settings.skirt_damping,
            'angular_damping': settings.skirt_damping,
            'root_angle_deg': settings.skirt_root_angle,
            'leaf_angle_deg': settings.skirt_leaf_angle,
        }
    else:
        return {
            'radius_ratio': 0.15,
            'base_mass': 0.5,
            'friction': 0.5,
            'linear_damping': 0.5,
            'angular_damping': 0.5,
            'root_angle_deg': 10.0,
            'leaf_angle_deg': 30.0,
        }


classes = (
    MAKERIGIT_OT_auto_physics,
)
