# -*- coding: utf-8 -*-

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty
from ..utils import find_mmd_root, get_mmd_model, get_existing_rigids_by_bone, find_body_mesh
from ..constants import ANCHOR_BONE_MAP, REGION_DEFAULT_COLLISION_GROUP


class MAKERIGIT_OT_region_physics(bpy.types.Operator):
    bl_idname = 'makerigit.region_physics'
    bl_label = 'Generate Region Physics'
    bl_description = 'Generate physics for a specific body region'
    bl_options = {'REGISTER', 'UNDO'}

    region: bpy.props.EnumProperty(
        name='Region',
        items=[
            ('HAIR', 'Hair', 'Hair chains from 頭'),
            ('SKIRT', 'Skirt', 'Skirt chains from 下半身'),
            ('SLEEVE_L', 'Left Sleeve', 'Left sleeve from 手首.L'),
            ('SLEEVE_R', 'Right Sleeve', 'Right sleeve from 手首.R'),
            ('TAIL', 'Tail', 'Tail chains'),
            ('CUSTOM', 'Custom', 'Custom anchor bone'),
        ],
    )
    anchor_bones: StringProperty(name='Anchor Bones', default='',
                                 description='Comma-separated anchor bone names (for Custom)')
    radius_ratio: FloatProperty(name='Radius Ratio', default=0.15, min=0.01, max=1.0)
    base_mass: FloatProperty(name='Base Mass', default=0.5, min=0.001, max=10.0)
    friction: FloatProperty(name='Friction', default=0.5, min=0.0, max=1.0)
    damping: FloatProperty(name='Damping', default=0.5, min=0.0, max=1.0)
    root_angle: FloatProperty(name='Root Angle', default=10.0, min=0.0, max=90.0, subtype='ANGLE')
    leaf_angle: FloatProperty(name='Leaf Angle', default=30.0, min=0.0, max=180.0, subtype='ANGLE')
    collision_group: IntProperty(name='Collision Group', default=2, min=0, max=15)
    fit_to_mesh: BoolProperty(name='Fit to Mesh', default=True)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        if self.region != 'CUSTOM':
            self.collision_group = REGION_DEFAULT_COLLISION_GROUP.get(self.region, 6)
        return context.window_manager.invoke_props_dialog(self, width=300)

    def execute(self, context):
        root = find_mmd_root(context.active_object)
        if root is None:
            self.report({'ERROR'}, 'No MMD model found')
            return {'CANCELLED'}

        model = get_mmd_model(root)
        arm = model.armature()

        from ..core.chain_detector import detect_chains_for_region
        from ..core.rigid_generator import create_rigids_for_chain
        from ..core.joint_generator import create_joints_for_chain
        from ..core.mesh_fitter import fit_rigid_to_mesh

        if self.region == 'CUSTOM':
            anchor_set = frozenset(n.strip() for n in self.anchor_bones.split(',') if n.strip())
            if not anchor_set:
                self.report({'ERROR'}, 'No anchor bones specified')
                return {'CANCELLED'}
        else:
            anchor_set = ANCHOR_BONE_MAP.get(self.region)

        chains = detect_chains_for_region(arm, self.region, anchor_set)
        if not chains:
            self.report({'WARNING'}, f'No dynamic chains found for {self.region}')
            return {'CANCELLED'}

        existing = get_existing_rigids_by_bone(model)
        mask = [False] * 16
        mask[0] = True
        if self.collision_group > 0:
            mask[self.collision_group - 1] = True

        total_rigids = 0
        total_joints = 0

        for chain_info in chains:
            bone_to_rigid, n_r = create_rigids_for_chain(
                model, arm, chain_info,
                skip_existing=existing,
                radius_ratio=self.radius_ratio,
                base_mass=self.base_mass,
                friction=self.friction,
                linear_damping=self.damping,
                angular_damping=self.damping,
                collision_group=self.collision_group,
                collision_mask=mask,
            )
            n_j = create_joints_for_chain(
                model, arm, chain_info, bone_to_rigid,
                root_angle_deg=self.root_angle,
                leaf_angle_deg=self.leaf_angle,
            )
            total_rigids += n_r
            total_joints += n_j
            existing.update(bone_to_rigid)

            if self.fit_to_mesh:
                fallback_mesh = find_body_mesh(root)
                if fallback_mesh:
                    for bone in chain_info['chain']:
                        rigid = bone_to_rigid.get(bone.name)
                        if rigid:
                            shape = rigid.mmd_rigid.shape
                            fit_rigid_to_mesh(rigid, arm, fallback_mesh,
                                              bone.name, shape)

        self.report({'INFO'},
                    f'{self.region}: {total_rigids} rigids, {total_joints} joints created')
        return {'FINISHED'}


classes = (
    MAKERIGIT_OT_region_physics,
)
