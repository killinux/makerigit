# -*- coding: utf-8 -*-

import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty, StringProperty
from ..utils import find_mmd_root, get_mmd_model


class MAKERIGIT_OT_breast_apply(bpy.types.Operator):
    bl_idname = 'makerigit.breast_apply'
    bl_label = 'Apply Breast Physics'
    bl_description = 'Create or recreate breast physics with current settings'
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

        from ..core.breast_physics import create_breast_physics

        n_r, n_j, skipped = create_breast_physics(
            model, arm, root,
            preset_name=settings.breast_preset if settings.breast_preset != 'CUSTOM' else None,
            shape=settings.breast_shape,
            auto_fit_size=settings.breast_auto_fit,
            size_multiplier=settings.breast_size_mult,
            collision_group=15,
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

        msg = f'Breast: {n_r} rigids, {n_j} joints'
        if skipped:
            msg += f' (skipped: {", ".join(skipped)})'
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class MAKERIGIT_OT_breast_reset_preset(bpy.types.Operator):
    bl_idname = 'makerigit.breast_reset_preset'
    bl_label = 'Reset to Preset'
    bl_description = 'Reset breast parameters to the selected preset values'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..constants import BREAST_PRESETS
        settings = context.scene.makerigit_settings
        preset = settings.breast_preset
        if preset == 'CUSTOM':
            self.report({'WARNING'}, 'No preset selected to reset to')
            return {'CANCELLED'}

        params = BREAST_PRESETS.get(preset)
        if params is None:
            return {'CANCELLED'}

        settings.breast_mass = params['mass']
        settings.breast_friction = params['friction']
        settings.breast_linear_damping = params['linear_damping']
        settings.breast_angular_damping = params['angular_damping']
        settings.breast_bounce = params['bounce']
        settings.breast_limit_x = params['limit_x']
        settings.breast_limit_y = params['limit_y']
        settings.breast_limit_z = params['limit_z']
        settings.breast_spring_ang_x = params['spring_ang_x']
        settings.breast_spring_ang_y = params['spring_ang_y']
        settings.breast_spring_ang_z = params['spring_ang_z']
        settings.breast_spring_lin_x = params['spring_lin_x']
        settings.breast_spring_lin_y = params['spring_lin_y']
        settings.breast_spring_lin_z = params['spring_lin_z']

        self.report({'INFO'}, f'Reset to {preset} preset')
        return {'FINISHED'}


classes = (
    MAKERIGIT_OT_breast_apply,
    MAKERIGIT_OT_breast_reset_preset,
)
