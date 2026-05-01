# -*- coding: utf-8 -*-

from ..constants import (
    CANONICAL_BODY_BONES, ANCHOR_BONE_MAP, BREAST_BONE_PATTERNS,
    REGION_DEFAULT_COLLISION_GROUP,
)
from ..utils import is_internal_helper_bone


def _matches_breast_pattern(name):
    for pat in BREAST_BONE_PATTERNS:
        if pat in name:
            return True
    return False


def detect_all_chains(arm, anchor_overrides=None, min_chain_length=2):
    regions = {}
    for region_name, anchors in ANCHOR_BONE_MAP.items():
        if region_name == 'BREAST':
            continue
        actual_anchors = anchors
        if anchor_overrides and region_name in anchor_overrides:
            actual_anchors = frozenset(anchor_overrides[region_name])
        chains = _detect_chains(arm, actual_anchors, min_chain_length)
        if chains:
            regions[region_name] = chains

    breast_chains = _detect_breast_chains(arm)
    if breast_chains:
        regions['BREAST'] = breast_chains

    return regions


def detect_chains_for_region(arm, region_name, anchor_bones=None,
                             min_chain_length=2):
    if region_name == 'BREAST':
        return _detect_breast_chains(arm)

    if anchor_bones is None:
        anchor_bones = ANCHOR_BONE_MAP.get(region_name, frozenset())
    return _detect_chains(arm, anchor_bones, min_chain_length)


def _detect_chains(arm, anchor_bones, min_chain_length):
    chains = []
    for bone in arm.data.bones:
        if bone.name in CANONICAL_BODY_BONES:
            continue
        if is_internal_helper_bone(bone.name):
            continue
        if _matches_breast_pattern(bone.name):
            continue
        parent = bone.parent
        if parent is None or parent.name not in anchor_bones:
            continue

        subtree = []
        depth_by_name = {}
        stack = [(bone, 0)]
        while stack:
            cur, d = stack.pop()
            if cur is not bone and cur.name in CANONICAL_BODY_BONES:
                continue
            if is_internal_helper_bone(cur.name):
                continue
            subtree.append(cur)
            depth_by_name[cur.name] = d
            for ch in cur.children:
                stack.append((ch, d + 1))

        if len(subtree) < min_chain_length:
            continue

        max_depth = max(depth_by_name.values()) if depth_by_name else 0
        side = _classify_side(bone.name)

        chains.append({
            'root': bone,
            'chain': subtree,
            'depth_by_name': depth_by_name,
            'max_depth': max_depth,
            'side': side,
            'parent_body_bone': parent.name,
        })
    return chains


def _detect_breast_chains(arm):
    chains = []
    for bone in arm.data.bones:
        if not _matches_breast_pattern(bone.name):
            continue
        if bone.parent is None:
            continue
        side = _classify_side(bone.name)

        subtree = [bone]
        depth_by_name = {bone.name: 0}
        d = 1
        for ch in bone.children_recursive:
            subtree.append(ch)
            depth_by_name[ch.name] = d
            d += 1

        chains.append({
            'root': bone,
            'chain': subtree,
            'depth_by_name': depth_by_name,
            'max_depth': max(depth_by_name.values()) if depth_by_name else 0,
            'side': side,
            'parent_body_bone': bone.parent.name,
        })
    return chains


def _classify_side(name):
    if name.endswith('.L') or name.startswith('左'):
        return 'L'
    if name.endswith('.R') or name.startswith('右'):
        return 'R'
    return 'CENTER'
