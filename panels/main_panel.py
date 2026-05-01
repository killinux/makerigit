# -*- coding: utf-8 -*-

import bpy
from ..utils import find_mmd_root, get_mmd_model


def _count_children_by_type(root, mmd_type):
    count = 0
    for obj in root.children_recursive:
        if getattr(obj, 'mmd_type', '') == mmd_type:
            count += 1
    return count


class _MakeRigitPanelBase:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MakeRigit'


class MAKERIGIT_PT_main(_MakeRigitPanelBase, bpy.types.Panel):
    bl_label = 'MakeRigit'
    bl_idname = 'MAKERIGIT_PT_main'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.makerigit_settings

        obj = context.active_object
        root = find_mmd_root(obj) if obj else None

        if root is None:
            layout.label(text='Select an MMD model', icon='ERROR')
            return

        model = get_mmd_model(root)
        arm = model.armature()
        n_bones = len(arm.data.bones) if arm else 0
        n_rigids = _count_children_by_type(root, 'RIGID_BODY')
        n_joints = _count_children_by_type(root, 'JOINT')

        layout.label(text=f'Model: {root.name}')
        row = layout.row()
        row.label(text=f'Bones: {n_bones}')
        row.label(text=f'Rigids: {n_rigids}')
        row.label(text=f'Joints: {n_joints}')

        layout.separator()
        layout.operator('makerigit.auto_physics', icon='PHYSICS')

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(settings, 'include_hair', toggle=True)
        row.prop(settings, 'include_skirt', toggle=True)
        row.prop(settings, 'include_sleeve', toggle=True)
        row = col.row(align=True)
        row.prop(settings, 'include_breast', toggle=True)
        row.prop(settings, 'include_other', toggle=True)

        layout.separator()
        row = layout.row(align=True)
        row.prop(settings, 'fit_to_mesh')
        row.prop(settings, 'build_rig_after')


class MAKERIGIT_PT_regions(_MakeRigitPanelBase, bpy.types.Panel):
    bl_label = 'Region Parameters'
    bl_idname = 'MAKERIGIT_PT_regions'
    bl_parent_id = 'MAKERIGIT_PT_main'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout


class MAKERIGIT_PT_hair(_MakeRigitPanelBase, bpy.types.Panel):
    bl_label = 'Hair'
    bl_idname = 'MAKERIGIT_PT_hair'
    bl_parent_id = 'MAKERIGIT_PT_regions'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.makerigit_settings

        col = layout.column(align=True)
        col.prop(settings, 'hair_radius_ratio')
        col.prop(settings, 'hair_root_angle')
        col.prop(settings, 'hair_leaf_angle')
        col.prop(settings, 'hair_collision_group')
        col.prop(settings, 'hair_mass')
        col.prop(settings, 'hair_damping')

        layout.separator()
        op = layout.operator('makerigit.region_physics', text='Generate Hair Physics')
        op.region = 'HAIR'


class MAKERIGIT_PT_skirt(_MakeRigitPanelBase, bpy.types.Panel):
    bl_label = 'Skirt'
    bl_idname = 'MAKERIGIT_PT_skirt'
    bl_parent_id = 'MAKERIGIT_PT_regions'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.makerigit_settings

        col = layout.column(align=True)
        col.prop(settings, 'skirt_radius_ratio')
        col.prop(settings, 'skirt_root_angle')
        col.prop(settings, 'skirt_leaf_angle')
        col.prop(settings, 'skirt_collision_group')
        col.prop(settings, 'skirt_mass')
        col.prop(settings, 'skirt_damping')

        layout.separator()
        op = layout.operator('makerigit.region_physics', text='Generate Skirt Physics')
        op.region = 'SKIRT'


class MAKERIGIT_PT_sleeve(_MakeRigitPanelBase, bpy.types.Panel):
    bl_label = 'Sleeve'
    bl_idname = 'MAKERIGIT_PT_sleeve'
    bl_parent_id = 'MAKERIGIT_PT_regions'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        op = row.operator('makerigit.region_physics', text='Left Sleeve')
        op.region = 'SLEEVE_L'
        op = row.operator('makerigit.region_physics', text='Right Sleeve')
        op.region = 'SLEEVE_R'


class MAKERIGIT_PT_custom(_MakeRigitPanelBase, bpy.types.Panel):
    bl_label = 'Custom'
    bl_idname = 'MAKERIGIT_PT_custom'
    bl_parent_id = 'MAKERIGIT_PT_regions'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        layout.label(text='Comma-separated anchor bones:')
        op = layout.operator('makerigit.region_physics', text='Generate Custom Physics')
        op.region = 'CUSTOM'


class MAKERIGIT_PT_breast(_MakeRigitPanelBase, bpy.types.Panel):
    bl_label = 'Breast Physics'
    bl_idname = 'MAKERIGIT_PT_breast'
    bl_parent_id = 'MAKERIGIT_PT_main'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.makerigit_settings

        layout.prop(settings, 'breast_preset')

        layout.separator()
        col = layout.column(align=True)
        col.prop(settings, 'breast_mass')
        col.prop(settings, 'breast_friction')
        col.prop(settings, 'breast_bounce')
        col.prop(settings, 'breast_linear_damping')
        col.prop(settings, 'breast_angular_damping')

        layout.separator()
        layout.label(text='Rotation Limits (degrees):')
        col = layout.column(align=True)
        col.prop(settings, 'breast_limit_x', text='X')
        col.prop(settings, 'breast_limit_y', text='Y')
        col.prop(settings, 'breast_limit_z', text='Z')

        layout.separator()
        layout.label(text='Spring Angular:')
        row = layout.row(align=True)
        row.prop(settings, 'breast_spring_ang_x', text='X')
        row.prop(settings, 'breast_spring_ang_y', text='Y')
        row.prop(settings, 'breast_spring_ang_z', text='Z')

        layout.label(text='Spring Linear:')
        row = layout.row(align=True)
        row.prop(settings, 'breast_spring_lin_x', text='X')
        row.prop(settings, 'breast_spring_lin_y', text='Y')
        row.prop(settings, 'breast_spring_lin_z', text='Z')

        layout.separator()
        col = layout.column(align=True)
        col.prop(settings, 'breast_shape')
        col.prop(settings, 'breast_auto_fit')
        if not settings.breast_auto_fit:
            col.prop(settings, 'breast_size_mult')

        layout.separator()
        layout.operator('makerigit.breast_apply', icon='PHYSICS')
        layout.operator('makerigit.breast_reset_preset', icon='FILE_REFRESH')


class MAKERIGIT_PT_presets(_MakeRigitPanelBase, bpy.types.Panel):
    bl_label = 'Presets'
    bl_idname = 'MAKERIGIT_PT_presets'
    bl_parent_id = 'MAKERIGIT_PT_main'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        layout.operator('makerigit.save_preset', icon='FILE_NEW')
        layout.operator('makerigit.load_preset', icon='FILE_FOLDER')
        layout.operator('makerigit.delete_preset', icon='TRASH')


class MAKERIGIT_PT_cleanup(_MakeRigitPanelBase, bpy.types.Panel):
    bl_label = 'Cleanup'
    bl_idname = 'MAKERIGIT_PT_cleanup'
    bl_parent_id = 'MAKERIGIT_PT_main'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        layout.operator('makerigit.remove_all_physics', icon='TRASH')

        layout.separator()
        col = layout.column(align=True)
        for region, label in [('HAIR', 'Hair Only'), ('SKIRT', 'Skirt Only'),
                               ('SLEEVE', 'Sleeve Only'), ('BREAST', 'Breast Only')]:
            op = col.operator('makerigit.remove_region_physics', text=f'Remove {label}')
            op.region = region


classes = (
    MAKERIGIT_PT_main,
    MAKERIGIT_PT_regions,
    MAKERIGIT_PT_hair,
    MAKERIGIT_PT_skirt,
    MAKERIGIT_PT_sleeve,
    MAKERIGIT_PT_custom,
    MAKERIGIT_PT_breast,
    MAKERIGIT_PT_presets,
    MAKERIGIT_PT_cleanup,
)
