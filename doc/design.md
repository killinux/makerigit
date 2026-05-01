# MakeRigit 设计文档

## 1. 项目概述

MakeRigit 是一个 Blender 3.6 插件，能够为任意 PMX 模型自动添加物理刚体和关节约束。
参考 PMXEditor 的设计原理，复用已安装的 mmd_tools 插件 API。

### 核心目标
- 一键为任意 PMX 模型生成完整物理（头发、裙子、袖子、胸部等）
- 按区域（Region）独立控制物理参数
- 胸部物理提供极致的精细控制（预设 + 全自定义）
- 预设系统，保存/加载物理配置

## 2. PMXEditor 物理原理参考

### 2.1 刚体数据结构（PMX 格式）

| 字段 | 类型 | 说明 |
|------|------|------|
| name | text | 刚体名称（日/英） |
| bone_index | index | 关联骨骼 |
| group_id | byte(0-15) | 碰撞组 |
| non_collision_group | 16-bit mask | 非碰撞组掩码（bit=1 表示不碰撞） |
| shape | byte | 0=球, 1=盒, 2=胶囊 |
| size | vec3 | 形状尺寸 |
| position | vec3 | 相对骨骼位置 |
| rotation | vec3 | 欧拉角（弧度） |
| mass | float | 质量 |
| move_damping | float | 移动衰减 |
| rotation_damping | float | 旋转衰减 |
| repulsion | float | 弹性（反弹） |
| friction | float | 摩擦力 |
| physics_mode | byte | 0=跟随骨骼, 1=物理演算, 2=物理+骨骼 |

### 2.2 关节数据结构

| 字段 | 类型 | 说明 |
|------|------|------|
| name | text | 关节名称 |
| rigid_body_a/b | index | 连接的两个刚体 |
| position | vec3 | 关节世界坐标 |
| rotation | vec3 | 关节旋转 |
| position_limit_min/max | vec3 | 移动限制 |
| rotation_limit_min/max | vec3 | 旋转限制（弧度） |
| spring_position | vec3 | 弹簧移动常数 |
| spring_rotation | vec3 | 弹簧旋转常数 |

### 2.3 PMXEditor 自动生成逻辑

PMXEditor 提供两种自动生成命令：

**1. 创建刚体 - 骨骼追踪（Bone Tracking）**
- 生成静态刚体，跟随骨骼运动
- 用于主体骨架（身体、手臂、腿）

**2. 创建刚体/关联关节（Linked Joint）**
- 同时生成动态刚体 + 连接关节
- 根据骨骼长度自动计算尺寸
- 默认形状：胶囊体
- 默认旋转限制：每轴 ±10°
- 默认移动限制：全零
- 默认弹簧常数：全零
- 命名：与骨骼同名

**关键设计原则：**
- 链根 = 静态(STATIC)，链中/尾 = 动态(DYNAMIC)
- 胶囊高度 = 骨骼长度
- 胶囊半径 ∝ 骨骼长度
- 关节位于子骨骼头部（= 父骨骼尾部）
- 质量沿链递减

## 3. 插件架构

### 3.1 目录结构

```
makerigit/
├── __init__.py              # bl_info, register/unregister, MakeRigitSettings
├── constants.py             # 常量定义
├── utils.py                 # 工具函数
├── core/
│   ├── __init__.py
│   ├── chain_detector.py    # 骨骼链检测引擎
│   ├── rigid_generator.py   # 刚体生成器
│   ├── joint_generator.py   # 关节生成器
│   ├── breast_physics.py    # 胸部物理专用引擎
│   └── mesh_fitter.py       # 网格匹配（刚体尺寸拟合）
├── operators/
│   ├── __init__.py
│   ├── auto_physics.py      # 一键全身物理
│   ├── region_physics.py    # 按区域生成
│   ├── breast_ops.py        # 胸部物理专用操作
│   ├── cleanup.py           # 清理/删除物理
│   └── preset_ops.py        # 预设保存/加载
├── panels/
│   ├── __init__.py
│   └── main_panel.py        # N面板 UI
├── presets/                  # 内置预设 JSON
│   ├── breast_subtle.json
│   ├── breast_natural.json
│   ├── breast_bouncy.json
│   ├── breast_dramatic.json
│   ├── hair_default.json
│   └── skirt_default.json
└── doc/
    └── design.md            # 本文件
```

### 3.2 依赖关系

```
__init__.py
  ├── panels/main_panel.py
  │     └── operators/*
  └── MakeRigitSettings (PropertyGroup)

operators/*
  └── core/*
        ├── chain_detector.py  ← constants.py, utils.py
        ├── rigid_generator.py ← utils.py, mesh_fitter.py
        ├── joint_generator.py ← utils.py
        ├── breast_physics.py  ← rigid_generator, joint_generator, mesh_fitter
        └── mesh_fitter.py     ← utils.py

utils.py ← mmd_tools.core.model.Model
constants.py ← (无外部依赖)
```

### 3.3 mmd_tools 复用点

| 用途 | mmd_tools 接口 |
|------|----------------|
| 模型包装 | `mmd_tools.core.model.Model(root_obj)` |
| 创建刚体 | `model.createRigidBody(**kwargs)` |
| 创建关节 | `model.createJoint(**kwargs)` |
| 遍历刚体 | `model.rigidBodies()` |
| 遍历关节 | `model.joints()` |
| 获取骨架 | `model.armature()` |
| 形状常量 | `rigid_body.SHAPE_SPHERE/BOX/CAPSULE` |
| 模式常量 | `rigid_body.MODE_STATIC/DYNAMIC/DYNAMIC_BONE` |
| 构建物理 | `bpy.ops.mmd_tools.build_rig()` |
| 清理物理 | `bpy.ops.mmd_tools.clean_rig()` |

## 4. 核心算法

### 4.1 骨骼链检测 (`chain_detector.py`)

参考 PMXEditor 的思路：从锚点骨骼出发，沿子骨骼树遍历，检测动态链。

**区域-锚点映射：**

| 区域 | 锚点骨骼 | 碰撞组(默认) |
|------|----------|-------------|
| 头发 HAIR | 頭 | 2 |
| 裙子 SKIRT | 下半身 | 3 |
| 左袖 SLEEVE_L | 手首.L | 4 |
| 右袖 SLEEVE_R | 手首.R | 4 |
| 胸部 BREAST | 上半身2 / 上半身 | 15 |
| 尾巴 TAIL | 下半身 / 尻 | 5 |

**检测算法：**

```
输入: mmd_root, armature
输出: { RegionType -> [ChainInfo] }

对骨架中每个骨骼:
    跳过 canonical body bones（标准MMD骨骼）
    跳过 _dummy_* / _shadow_*（mmd_tools内部骨骼）
    跳过无父骨骼的

    判断区域: 父骨骼名 → 匹配锚点映射
    特殊: 胸部按骨骼名匹配（含"乳奶"/"胸"/"おっぱい"）

    BFS 收集子树（跳过canonical和helper骨骼）
    记录每骨骼深度

    子树大小 >= min_chain_length (默认2, 胸部=1):
        加入对应区域的链列表
        元数据: root, chain[], depth_by_name{}, max_depth, side(L/R/center)
```

### 4.2 刚体生成 (`rigid_generator.py`)

参考 PMXEditor 的 "创建刚体/关联关节" 逻辑：

```
对链中每个骨骼:
    bone_length = max(bone.length, 0.01)
    radius = max(bone_length * radius_ratio, 0.005)

    形状选择:
        有子骨骼 → CAPSULE, size=(radius, bone_length, 0)
        叶子骨骼 → SPHERE, size=(radius, 0, 0)

    位置 = 骨骼世界空间中点 (head + tail) / 2
    旋转 = 骨骼世界矩阵的 YXZ 欧拉角

    动力学类型:
        链根 → STATIC (跟随骨骼)
        其他 → DYNAMIC (物理演算)

    质量递减: mass = base_mass * (mass_decay ^ depth)
        默认 base_mass=0.5, mass_decay=0.8

    调用 model.createRigidBody(...)
```

### 4.3 关节生成 (`joint_generator.py`)

```
对链中每对 父-子 刚体:
    位置 = 子骨骼头部（世界坐标）
    旋转 = 子骨骼世界矩阵 YXZ 欧拉角

    角度限制插值 (PMXEditor默认 ±10°, 本插件增强):
        t = depth / max_depth
        angle = lerp(root_angle_deg, leaf_angle_deg, t)
        → 根部紧（10°），末端松（30°）

    移动限制 = (0,0,0) 全锁定
    弹簧常数 = (0,0,0) 默认无弹簧

    调用 model.createJoint(...)
```

### 4.4 网格拟合 (`mesh_fitter.py`)

根据网格顶点权重，将刚体半径收缩到与实际网格厚度匹配：

```
输入: rigid_obj, armature, mesh, bone_name, shape
输出: 调整后的尺寸 (或 None)

1. 查找骨骼的顶点组（含别名，如 足D.L → 足.L）
2. 收集权重 > 0.3 的顶点
3. 计算每个顶点到骨骼Y轴的垂直距离
4. 取 90% 分位数作为 measured_r
5. new_r = min(template_r, measured_r * pad)  // 只缩不扩
6. 更新刚体尺寸
```

## 5. 胸部物理精细控制

### 5.1 设计理念

胸部物理是本插件的核心差异化功能。不同于通用链物理的简单参数，
胸部提供独立的、逐轴的精细控制，满足从"微妙自然"到"夸张弹跳"的各种需求。

### 5.2 参数体系

```python
BreastPhysicsParams:
    # 刚体参数
    shape: SPHERE | CAPSULE           # 球体推荐（短骨骼更适合）
    mass: float                        # 质量
    friction: float                    # 摩擦力
    linear_damping: float              # 线性阻尼
    angular_damping: float             # 角度阻尼
    bounce: float                      # 弹性（反弹系数）
    collision_group: int = 15          # 碰撞组（隔离）
    auto_fit_size: bool                # 自动拟合网格大小
    size_multiplier: float             # 手动大小倍率

    # 关节限制（每轴独立, 角度制）
    limit_x: (min_deg, max_deg)        # X轴旋转限制
    limit_y: (min_deg, max_deg)        # Y轴旋转限制
    limit_z: (min_deg, max_deg)        # Z轴旋转限制

    # 弹簧常数（每轴独立）
    spring_angular: (x, y, z)          # 角度弹簧（回弹刚度）
    spring_linear: (x, y, z)           # 线性弹簧
```

### 5.3 内置预设

| 预设 | mass | lin_damp | ang_damp | bounce | limit_x | limit_y | limit_z | spring_ang |
|------|------|----------|----------|--------|---------|---------|---------|-----------|
| Subtle | 0.8 | 0.8 | 0.8 | 0.1 | ±8° | ±5° | ±8° | (100,100,100) |
| Natural | 1.0 | 0.5 | 0.5 | 0.3 | ±15° | ±10° | ±15° | (50,50,50) |
| Bouncy | 1.2 | 0.3 | 0.3 | 0.6 | ±25° | ±15° | ±25° | (20,20,20) |
| Dramatic | 1.5 | 0.2 | 0.2 | 0.8 | ±35° | ±20° | ±35° | (10,10,10) |

**设计思路：**
- 高阻尼 + 窄角度 + 高弹簧 = 微妙自然
- 低阻尼 + 宽角度 + 低弹簧 = 夸张弹跳
- bounce（反弹系数）控制碰撞后的回弹力度
- spring_angular 越高，回到静止位越快（刚度）

### 5.4 胸部物理生成算法

```
1. 查找胸部骨骼: 乳奶.L / 乳奶.R（或备选名称）
2. 查找锚点骨骼: 上半身2 > 上半身 > 上半身3
3. 锚点刚体:
   - 已存在 → 复用
   - 不存在 → 创建 STATIC 刚体
4. 对每个胸部骨骼:
   a. 位置 = 骨骼世界中点
   b. 旋转 = 骨骼世界矩阵
   c. 大小:
      auto_fit=true  → mesh_fitter 测量胸部顶点范围
      auto_fit=false → bone_length * size_multiplier
   d. 创建 DYNAMIC 刚体 (BreastPhysicsParams)
   e. 创建关节: 锚点刚体 ↔ 胸部刚体
      - 每轴独立的旋转限制
      - 每轴独立的弹簧常数
```

## 6. UI 设计

### 6.1 面板布局

位置: 3D视口 → 侧边栏(N) → "MakeRigit" 标签页

```
┌─────────────────────────────┐
│ MakeRigit                   │
├─────────────────────────────┤
│ 模型: [当前选中的MMD模型名]    │
│ 骨骼数: XX  现有刚体: XX      │
│                             │
│ ┌─────────────────────────┐ │
│ │  ⚡ 一键生成全身物理      │ │
│ └─────────────────────────┘ │
│ ☑ 头发  ☑ 裙子  ☑ 袖子     │
│ ☑ 胸部  ☑ 其他             │
│ ☑ 拟合网格  ☑ 生成后构建    │
├─────────────────────────────┤
│ ▸ 区域参数                   │ (可展开)
│   ▸ 头发                    │
│     锚点: [頭]              │
│     半径比: [0.15]          │
│     根部角度: [10°]         │
│     末端角度: [30°]         │
│     碰撞组: [2]             │
│     [生成头发物理]           │
│   ▸ 裙子 (类似)             │
│   ▸ 袖子 (类似)             │
│   ▸ 自定义                  │
│     锚点骨骼: [          ]  │
│     [生成]                  │
├─────────────────────────────┤
│ ▾ 胸部物理                   │ (默认展开)
│   预设: [Natural ▾]         │
│                             │
│   质量: [====1.0=========]  │
│   摩擦: [====0.5=========]  │
│   弹性: [====0.3=========]  │
│   线性阻尼: [====0.5=====]  │
│   角度阻尼: [====0.5=====]  │
│                             │
│   ── 旋转限制 ──             │
│   X: [-15° ~ 15°]          │
│   Y: [-10° ~ 10°]          │
│   Z: [-15° ~ 15°]          │
│                             │
│   ── 弹簧常数 ──             │
│   角度 X/Y/Z: [50] [50] [50]│
│   线性 X/Y/Z: [0]  [0]  [0] │
│                             │
│   形状: [Sphere ▾]          │
│   ☑ 自动拟合大小             │
│   大小倍率: [1.0]           │
│                             │
│   [应用胸部物理]             │
│   [重置为预设值]             │
├─────────────────────────────┤
│ ▸ 预设管理                   │
│   名称: [my_preset]         │
│   [保存当前配置]             │
│   预设列表: [...]           │
│   [加载] [删除]             │
├─────────────────────────────┤
│ ▸ 清理                      │
│   [删除全部物理]             │
│   [仅删除头发物理]           │
│   [仅删除胸部物理]           │
│   [仅删除裙子物理]           │
└─────────────────────────────┘
```

### 6.2 PropertyGroup 设计

```python
class MakeRigitSettings(PropertyGroup):
    # 全局开关
    include_hair: BoolProperty(default=True)
    include_skirt: BoolProperty(default=True)
    include_sleeve: BoolProperty(default=True)
    include_breast: BoolProperty(default=True)
    include_other: BoolProperty(default=True)
    fit_to_mesh: BoolProperty(default=True)
    build_rig_after: BoolProperty(default=True)

    # 头发区域参数
    hair_radius_ratio: FloatProperty(default=0.15, min=0.05, max=0.5)
    hair_root_angle: FloatProperty(default=10.0, min=0, max=90)
    hair_leaf_angle: FloatProperty(default=30.0, min=0, max=180)
    hair_collision_group: IntProperty(default=2, min=0, max=15)
    hair_mass: FloatProperty(default=0.5, min=0.001, max=10)
    hair_damping: FloatProperty(default=0.5, min=0, max=1)
    # ... 裙子/袖子类似

    # 胸部参数 (全量)
    breast_preset: EnumProperty(items=[
        ('SUBTLE', 'Subtle', '微妙自然'),
        ('NATURAL', 'Natural', '自然平衡'),
        ('BOUNCY', 'Bouncy', '弹性活泼'),
        ('DRAMATIC', 'Dramatic', '夸张效果'),
        ('CUSTOM', 'Custom', '完全自定义'),
    ], default='NATURAL', update=on_breast_preset_change)
    breast_mass: FloatProperty(...)
    breast_friction: FloatProperty(...)
    breast_linear_damping: FloatProperty(...)
    breast_angular_damping: FloatProperty(...)
    breast_bounce: FloatProperty(...)
    breast_limit_x: FloatProperty(...)     # 角度制
    breast_limit_y: FloatProperty(...)
    breast_limit_z: FloatProperty(...)
    breast_spring_ang_x: FloatProperty(...)
    breast_spring_ang_y: FloatProperty(...)
    breast_spring_ang_z: FloatProperty(...)
    breast_spring_lin_x: FloatProperty(...)
    breast_spring_lin_y: FloatProperty(...)
    breast_spring_lin_z: FloatProperty(...)
    breast_shape: EnumProperty(...)
    breast_auto_fit: BoolProperty(default=True)
    breast_size_mult: FloatProperty(default=1.0)
```

## 7. 预设系统

### 7.1 JSON 格式

**完整预设（全身）:**

```json
{
    "version": 1,
    "name": "preset_name",
    "regions": {
        "hair": {
            "enabled": true,
            "anchor_bones": ["頭"],
            "radius_ratio": 0.15,
            "root_angle_deg": 10.0,
            "leaf_angle_deg": 30.0,
            "base_mass": 0.5,
            "mass_decay": 0.8,
            "friction": 0.5,
            "linear_damping": 0.5,
            "angular_damping": 0.5,
            "bounce": 0.0,
            "collision_group": 2
        },
        "skirt": { "..." : "..." },
        "sleeve": { "..." : "..." }
    },
    "breast": {
        "preset_name": "NATURAL",
        "shape": "SPHERE",
        "mass": 1.0,
        "friction": 0.5,
        "linear_damping": 0.5,
        "angular_damping": 0.5,
        "bounce": 0.3,
        "limit_x": [-15, 15],
        "limit_y": [-10, 10],
        "limit_z": [-15, 15],
        "spring_angular": [50, 50, 50],
        "spring_linear": [0, 0, 0],
        "auto_fit_size": true,
        "collision_group": 15
    }
}
```

### 7.2 存储位置

- 内置预设: `makerigit/presets/`（随插件分发）
- 用户预设: 同目录，用户可通过 UI 保存/加载/删除

## 8. 实现顺序

### Phase 1: 基础层（无内部依赖）
1. `constants.py` — 常量定义
2. `utils.py` — 工具函数
3. `core/__init__.py`

### Phase 2: 核心引擎（依赖 Phase 1）
4. `core/mesh_fitter.py` — 网格拟合
5. `core/chain_detector.py` — 链检测
6. `core/rigid_generator.py` — 刚体生成
7. `core/joint_generator.py` — 关节生成
8. `core/breast_physics.py` — 胸部物理

### Phase 3: 操作器（依赖 Phase 2）
9. `operators/__init__.py`
10. `operators/cleanup.py` — 清理（最简单，用于测试注册）
11. `operators/auto_physics.py` — 一键生成
12. `operators/region_physics.py` — 按区域生成
13. `operators/breast_ops.py` — 胸部操作
14. `operators/preset_ops.py` — 预设操作

### Phase 4: UI 和注册（依赖 Phase 3）
15. `panels/__init__.py`
16. `panels/main_panel.py` — UI 面板
17. `__init__.py` — 插件入口

### Phase 5: 预设数据文件
18. `presets/*.json`

## 9. 验证计划

### 功能测试
1. 加载任意 PMX 模型 → 一键生成 → 检查刚体/关节数量和位置
2. 按区域单独生成 → 检查只影响目标区域
3. 切换胸部预设 → 验证参数正确切换
4. 自定义胸部参数 → 验证预设自动切到 Custom
5. 保存预设 → 重新加载 → 验证参数一致
6. 清理全部/区域 → 验证只删除目标物理

### 兼容性测试
1. 无 mmd_tools 时 → 显示友好错误提示
2. 模型无胸部骨骼时 → 胸部面板隐藏或禁用
3. 模型已有物理时 → skip_if_exists 正常工作
4. Build Rig 后 → Blender 物理模拟正常运行

### 边界情况
1. 极短骨骼（length < 0.01）→ 最小尺寸兜底
2. 单骨骼链 → min_chain_length 过滤
3. 非标准骨骼命名 → 自定义锚点支持
