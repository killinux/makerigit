# -*- coding: utf-8 -*-

bl_info = {
    'name': 'MakeRigit',
    'author': 'MakeRigit',
    'version': (1, 0, 0),
    'blender': (3, 6, 0),
    'location': 'View3D > Sidebar > MakeRigit',
    'description': 'Auto-generate PMX physics rigid bodies and joints for any MMD model',
    'category': 'Object',
}

import bpy
from bpy.props import (
    BoolProperty, FloatProperty, IntProperty,
    EnumProperty, StringProperty, PointerProperty,
)

_mmd_tools_available = False
try:
    import mmd_tools
    _mmd_tools_available = True
except ImportError:
    pass


def _on_breast_preset_change(self, context):
    from .constants import BREAST_PRESETS
    preset = self.breast_preset
    if preset == 'CUSTOM':
        return
    params = BREAST_PRESETS.get(preset)
    if params is None:
        return
    self['breast_mass'] = params['mass']
    self['breast_friction'] = params['friction']
    self['breast_linear_damping'] = params['linear_damping']
    self['breast_angular_damping'] = params['angular_damping']
    self['breast_bounce'] = params['bounce']
    self['breast_limit_x'] = params['limit_x']
    self['breast_limit_y'] = params['limit_y']
    self['breast_limit_z'] = params['limit_z']
    self['breast_spring_ang_x'] = params['spring_ang_x']
    self['breast_spring_ang_y'] = params['spring_ang_y']
    self['breast_spring_ang_z'] = params['spring_ang_z']
    self['breast_spring_lin_x'] = params['spring_lin_x']
    self['breast_spring_lin_y'] = params['spring_lin_y']
    self['breast_spring_lin_z'] = params['spring_lin_z']


class MakeRigitSettings(bpy.types.PropertyGroup):
    # Global toggles
    include_hair: BoolProperty(name='Hair', default=True)
    include_skirt: BoolProperty(name='Skirt', default=True)
    include_sleeve: BoolProperty(name='Sleeve', default=True)
    include_breast: BoolProperty(name='Breast', default=True)
    include_other: BoolProperty(name='Other', default=True)
    fit_to_mesh: BoolProperty(name='Fit to Mesh', default=True)
    build_rig_after: BoolProperty(name='Build Rig After', default=False)

    # Hair
    hair_radius_ratio: FloatProperty(name='Radius Ratio', default=0.15, min=0.01, max=1.0)
    hair_root_angle: FloatProperty(name='Root Angle', default=10.0, min=0.0, max=90.0)
    hair_leaf_angle: FloatProperty(name='Leaf Angle', default=30.0, min=0.0, max=180.0)
    hair_collision_group: IntProperty(name='Collision Group', default=2, min=0, max=15)
    hair_mass: FloatProperty(name='Mass', default=0.5, min=0.001, max=10.0)
    hair_damping: FloatProperty(name='Damping', default=0.5, min=0.0, max=1.0)

    # Skirt
    skirt_radius_ratio: FloatProperty(name='Radius Ratio', default=0.15, min=0.01, max=1.0)
    skirt_root_angle: FloatProperty(name='Root Angle', default=10.0, min=0.0, max=90.0)
    skirt_leaf_angle: FloatProperty(name='Leaf Angle', default=30.0, min=0.0, max=180.0)
    skirt_collision_group: IntProperty(name='Collision Group', default=3, min=0, max=15)
    skirt_mass: FloatProperty(name='Mass', default=0.5, min=0.001, max=10.0)
    skirt_damping: FloatProperty(name='Damping', default=0.5, min=0.0, max=1.0)

    # Breast
    breast_preset: EnumProperty(
        name='Preset',
        items=[
            ('SUBTLE', 'Subtle', 'Minimal, professional movement'),
            ('NATURAL', 'Natural', 'Realistic, balanced physics'),
            ('BOUNCY', 'Bouncy', 'Anime-style bounce'),
            ('DRAMATIC', 'Dramatic', 'Maximum dramatic effect'),
            ('CUSTOM', 'Custom', 'Fully custom parameters'),
        ],
        default='NATURAL',
        update=_on_breast_preset_change,
    )
    breast_mass: FloatProperty(name='Mass', default=1.0, min=0.01, max=10.0)
    breast_friction: FloatProperty(name='Friction', default=0.5, min=0.0, max=1.0)
    breast_linear_damping: FloatProperty(name='Linear Damping', default=0.5, min=0.0, max=1.0)
    breast_angular_damping: FloatProperty(name='Angular Damping', default=0.5, min=0.0, max=1.0)
    breast_bounce: FloatProperty(name='Bounce', default=0.3, min=0.0, max=1.0)
    breast_limit_x: FloatProperty(name='Limit X', default=15.0, min=0.0, max=90.0)
    breast_limit_y: FloatProperty(name='Limit Y', default=10.0, min=0.0, max=90.0)
    breast_limit_z: FloatProperty(name='Limit Z', default=15.0, min=0.0, max=90.0)
    breast_spring_ang_x: FloatProperty(name='Spring Ang X', default=50.0, min=0.0, max=500.0)
    breast_spring_ang_y: FloatProperty(name='Spring Ang Y', default=50.0, min=0.0, max=500.0)
    breast_spring_ang_z: FloatProperty(name='Spring Ang Z', default=50.0, min=0.0, max=500.0)
    breast_spring_lin_x: FloatProperty(name='Spring Lin X', default=0.0, min=0.0, max=500.0)
    breast_spring_lin_y: FloatProperty(name='Spring Lin Y', default=0.0, min=0.0, max=500.0)
    breast_spring_lin_z: FloatProperty(name='Spring Lin Z', default=0.0, min=0.0, max=500.0)
    breast_shape: EnumProperty(
        name='Shape',
        items=[
            ('SPHERE', 'Sphere', 'Spherical collision shape'),
            ('CAPSULE', 'Capsule', 'Capsule collision shape'),
        ],
        default='SPHERE',
    )
    breast_auto_fit: BoolProperty(name='Auto Fit Size', default=True)
    breast_size_mult: FloatProperty(name='Size Multiplier', default=1.0, min=0.1, max=5.0)


from .operators.cleanup import classes as cleanup_classes
from .operators.auto_physics import classes as auto_classes
from .operators.region_physics import classes as region_classes
from .operators.breast_ops import classes as breast_classes
from .operators.preset_ops import classes as preset_classes
from .panels.main_panel import classes as panel_classes

_classes = (
    MakeRigitSettings,
    *cleanup_classes,
    *auto_classes,
    *region_classes,
    *breast_classes,
    *preset_classes,
    *panel_classes,
)


def register():
    if not _mmd_tools_available:
        print('[MakeRigit] WARNING: mmd_tools not found. Plugin will not function.')

    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.makerigit_settings = PointerProperty(type=MakeRigitSettings)


def unregister():
    del bpy.types.Scene.makerigit_settings

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
