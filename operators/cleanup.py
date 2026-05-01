# -*- coding: utf-8 -*-

import bpy
from bpy.props import EnumProperty
from ..utils import find_mmd_root, get_mmd_model


class MAKERIGIT_OT_remove_all_physics(bpy.types.Operator):
    bl_idname = 'makerigit.remove_all_physics'
    bl_label = 'Remove All Physics'
    bl_description = 'Remove all rigid bodies and joints from the active MMD model'
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
        removed_rigids = 0
        removed_joints = 0

        joints = list(model.joints())
        for j in joints:
            bpy.data.objects.remove(j, do_unlink=True)
            removed_joints += 1

        rigids = list(model.rigidBodies())
        for r in rigids:
            bpy.data.objects.remove(r, do_unlink=True)
            removed_rigids += 1

        self.report({'INFO'}, f'Removed {removed_rigids} rigid bodies, {removed_joints} joints')
        return {'FINISHED'}


class MAKERIGIT_OT_remove_region_physics(bpy.types.Operator):
    bl_idname = 'makerigit.remove_region_physics'
    bl_label = 'Remove Region Physics'
    bl_description = 'Remove physics for a specific region'
    bl_options = {'REGISTER', 'UNDO'}

    region: EnumProperty(
        name='Region',
        items=[
            ('HAIR', 'Hair', 'Remove hair physics'),
            ('SKIRT', 'Skirt', 'Remove skirt physics'),
            ('SLEEVE', 'Sleeve', 'Remove sleeve physics'),
            ('BREAST', 'Breast', 'Remove breast physics'),
        ],
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        from ..constants import REGION_DEFAULT_COLLISION_GROUP, BREAST_BONE_PATTERNS
        root = find_mmd_root(context.active_object)
        if root is None:
            self.report({'ERROR'}, 'No MMD model found')
            return {'CANCELLED'}

        model = get_mmd_model(root)

        if self.region == 'BREAST':
            target_bones = set()
            arm = model.armature()
            for bone in arm.data.bones:
                for pat in BREAST_BONE_PATTERNS:
                    if pat in bone.name:
                        target_bones.add(bone.name)
                        break
            rigids_to_remove = []
            rigid_names = set()
            for r in model.rigidBodies():
                if r.mmd_rigid.bone in target_bones:
                    rigids_to_remove.append(r)
                    rigid_names.add(r.name)

            joints_to_remove = []
            for j in model.joints():
                rbc = j.rigid_body_constraint
                if rbc and ((rbc.object1 and rbc.object1.name in rigid_names) or
                            (rbc.object2 and rbc.object2.name in rigid_names)):
                    joints_to_remove.append(j)
        else:
            group = REGION_DEFAULT_COLLISION_GROUP.get(self.region, -1)
            if self.region == 'SLEEVE':
                groups = {
                    REGION_DEFAULT_COLLISION_GROUP.get('SLEEVE_L', 4),
                    REGION_DEFAULT_COLLISION_GROUP.get('SLEEVE_R', 4),
                }
            else:
                groups = {group}

            rigids_to_remove = []
            rigid_names = set()
            for r in model.rigidBodies():
                if r.mmd_rigid.collision_group_number in groups:
                    rigids_to_remove.append(r)
                    rigid_names.add(r.name)

            joints_to_remove = []
            for j in model.joints():
                rbc = j.rigid_body_constraint
                if rbc and ((rbc.object1 and rbc.object1.name in rigid_names) or
                            (rbc.object2 and rbc.object2.name in rigid_names)):
                    joints_to_remove.append(j)

        for j in joints_to_remove:
            bpy.data.objects.remove(j, do_unlink=True)
        for r in rigids_to_remove:
            bpy.data.objects.remove(r, do_unlink=True)

        self.report({'INFO'},
                    f'Removed {len(rigids_to_remove)} rigids, {len(joints_to_remove)} joints '
                    f'for {self.region}')
        return {'FINISHED'}


classes = (
    MAKERIGIT_OT_remove_all_physics,
    MAKERIGIT_OT_remove_region_physics,
)
