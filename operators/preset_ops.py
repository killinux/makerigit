# -*- coding: utf-8 -*-

import bpy
import json
import os
from bpy.props import StringProperty, EnumProperty
from ..utils import find_mmd_root, get_mmd_model


def _presets_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                        'presets')


def _list_presets(self, context):
    d = _presets_dir()
    items = []
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.endswith('.json'):
                stem = os.path.splitext(name)[0]
                items.append((stem, stem, ''))
    if not items:
        items = [('__empty__', '(no presets)', '')]
    return items


class MAKERIGIT_OT_save_preset(bpy.types.Operator):
    bl_idname = 'makerigit.save_preset'
    bl_label = 'Save Preset'
    bl_description = 'Save current physics settings as a preset'
    bl_options = {'REGISTER'}

    preset_name: StringProperty(name='Preset Name', default='my_preset')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        settings = context.scene.makerigit_settings
        data = {
            'version': 1,
            'name': self.preset_name,
            'regions': {
                'hair': {
                    'radius_ratio': settings.hair_radius_ratio,
                    'root_angle_deg': settings.hair_root_angle,
                    'leaf_angle_deg': settings.hair_leaf_angle,
                    'collision_group': settings.hair_collision_group,
                    'base_mass': settings.hair_mass,
                    'damping': settings.hair_damping,
                },
                'skirt': {
                    'radius_ratio': settings.skirt_radius_ratio,
                    'root_angle_deg': settings.skirt_root_angle,
                    'leaf_angle_deg': settings.skirt_leaf_angle,
                    'collision_group': settings.skirt_collision_group,
                    'base_mass': settings.skirt_mass,
                    'damping': settings.skirt_damping,
                },
            },
            'breast': {
                'preset_name': settings.breast_preset,
                'shape': settings.breast_shape,
                'mass': settings.breast_mass,
                'friction': settings.breast_friction,
                'linear_damping': settings.breast_linear_damping,
                'angular_damping': settings.breast_angular_damping,
                'bounce': settings.breast_bounce,
                'limit_x': settings.breast_limit_x,
                'limit_y': settings.breast_limit_y,
                'limit_z': settings.breast_limit_z,
                'spring_ang_x': settings.breast_spring_ang_x,
                'spring_ang_y': settings.breast_spring_ang_y,
                'spring_ang_z': settings.breast_spring_ang_z,
                'spring_lin_x': settings.breast_spring_lin_x,
                'spring_lin_y': settings.breast_spring_lin_y,
                'spring_lin_z': settings.breast_spring_lin_z,
                'auto_fit': settings.breast_auto_fit,
                'size_mult': settings.breast_size_mult,
            },
        }

        d = _presets_dir()
        os.makedirs(d, exist_ok=True)
        filepath = os.path.join(d, f'{self.preset_name}.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.report({'INFO'}, f'Saved preset: {self.preset_name}')
        return {'FINISHED'}


class MAKERIGIT_OT_load_preset(bpy.types.Operator):
    bl_idname = 'makerigit.load_preset'
    bl_label = 'Load Preset'
    bl_description = 'Load physics settings from a preset'
    bl_options = {'REGISTER', 'UNDO'}

    preset: EnumProperty(name='Preset', items=_list_presets)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if self.preset == '__empty__':
            self.report({'WARNING'}, 'No presets available')
            return {'CANCELLED'}

        filepath = os.path.join(_presets_dir(), f'{self.preset}.json')
        if not os.path.isfile(filepath):
            self.report({'ERROR'}, f'Preset file not found: {filepath}')
            return {'CANCELLED'}

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        settings = context.scene.makerigit_settings

        hair = data.get('regions', {}).get('hair', {})
        if hair:
            settings.hair_radius_ratio = hair.get('radius_ratio', 0.15)
            settings.hair_root_angle = hair.get('root_angle_deg', 10.0)
            settings.hair_leaf_angle = hair.get('leaf_angle_deg', 30.0)
            settings.hair_collision_group = hair.get('collision_group', 2)
            settings.hair_mass = hair.get('base_mass', 0.5)
            settings.hair_damping = hair.get('damping', 0.5)

        skirt = data.get('regions', {}).get('skirt', {})
        if skirt:
            settings.skirt_radius_ratio = skirt.get('radius_ratio', 0.15)
            settings.skirt_root_angle = skirt.get('root_angle_deg', 10.0)
            settings.skirt_leaf_angle = skirt.get('leaf_angle_deg', 30.0)
            settings.skirt_collision_group = skirt.get('collision_group', 3)
            settings.skirt_mass = skirt.get('base_mass', 0.5)
            settings.skirt_damping = skirt.get('damping', 0.5)

        breast = data.get('breast', {})
        if breast:
            settings.breast_preset = breast.get('preset_name', 'NATURAL')
            settings.breast_shape = breast.get('shape', 'SPHERE')
            settings.breast_mass = breast.get('mass', 1.0)
            settings.breast_friction = breast.get('friction', 0.5)
            settings.breast_linear_damping = breast.get('linear_damping', 0.5)
            settings.breast_angular_damping = breast.get('angular_damping', 0.5)
            settings.breast_bounce = breast.get('bounce', 0.3)
            settings.breast_limit_x = breast.get('limit_x', 15.0)
            settings.breast_limit_y = breast.get('limit_y', 10.0)
            settings.breast_limit_z = breast.get('limit_z', 15.0)
            settings.breast_spring_ang_x = breast.get('spring_ang_x', 50.0)
            settings.breast_spring_ang_y = breast.get('spring_ang_y', 50.0)
            settings.breast_spring_ang_z = breast.get('spring_ang_z', 50.0)
            settings.breast_spring_lin_x = breast.get('spring_lin_x', 0.0)
            settings.breast_spring_lin_y = breast.get('spring_lin_y', 0.0)
            settings.breast_spring_lin_z = breast.get('spring_lin_z', 0.0)
            settings.breast_auto_fit = breast.get('auto_fit', True)
            settings.breast_size_mult = breast.get('size_mult', 1.0)

        self.report({'INFO'}, f'Loaded preset: {self.preset}')
        return {'FINISHED'}


class MAKERIGIT_OT_delete_preset(bpy.types.Operator):
    bl_idname = 'makerigit.delete_preset'
    bl_label = 'Delete Preset'
    bl_description = 'Delete a saved preset'
    bl_options = {'REGISTER'}

    preset: EnumProperty(name='Preset', items=_list_presets)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if self.preset == '__empty__':
            return {'CANCELLED'}
        filepath = os.path.join(_presets_dir(), f'{self.preset}.json')
        if os.path.isfile(filepath):
            os.remove(filepath)
            self.report({'INFO'}, f'Deleted preset: {self.preset}')
        return {'FINISHED'}


classes = (
    MAKERIGIT_OT_save_preset,
    MAKERIGIT_OT_load_preset,
    MAKERIGIT_OT_delete_preset,
)
