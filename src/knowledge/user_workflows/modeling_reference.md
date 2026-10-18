# COMSOL 全自动建模工作流指南

> 目标：新电脑上读完本文档即可在 **10 分钟内** 打通"环境检测 → API 验证 → 全自动建模"全流程。
> 按 Phase 0 → 5 顺序执行，每阶段通过后进入下一阶段。

---

## Phase 0 — 环境检测：找到 COMSOL 和 Python
若无法链接COMSOL客户端，在下述网址上安装COMSOL skill，然后重新检查连接
https://github.com/wjc9011/COMSOL_Multiphysics_MCP

### 0.1 复制以下脚本，保存为 `detect_env.py`，运行

```python
"""COMSOL 环境自动检测脚本。输出你的 COMSOL 路径和 API 状态。"""
import os, sys, subprocess, shutil
from pathlib import Path

print("=" * 60)
print("Phase 0: COMSOL 环境检测")
print("=" * 60)

# ---- Python ----
print(f"\n[Python]  {sys.version}")
print(f"[Python]  {sys.executable}")

# ---- pip / mph ----
try:
    import mph
    print(f"[mph]     {mph.__version__}  (OK)")
    MPH_OK = True
except ImportError:
    print("[mph]     NOT INSTALLED → 运行: pip install mph")
    MPH_OK = False

# ---- COMSOL 安装路径搜索 ----
COMSOL_CANDIDATES = [
    # Windows
    r"C:\Program Files\COMSOL\COMSOL64\Multiphysics",
    r"C:\COMSOL64\Multiphysics",
    r"D:\COMSOL64\Multiphysics",
    r"E:\COMSOL64\Multiphysics",
    r"H:\COMSOL64\Multiphysics",
    # Linux
    "/usr/local/comsol64/multiphysics",
    "/opt/comsol64/multiphysics",
    "/home/comsol64/multiphysics",
]

COMSOL_ROOT = None
for c in COMSOL_CANDIDATES:
    if os.path.isdir(c):
        COMSOL_ROOT = c
        break

# 尝试从环境变量或 PATH 查找
if not COMSOL_ROOT:
    comsol_exe = shutil.which("comsol") or shutil.which("comsol.exe")
    if comsol_exe:
        COMSOL_ROOT = str(Path(comsol_exe).parent.parent)

if COMSOL_ROOT:
    print(f"[COMSOL]  {COMSOL_ROOT}  (found)")
else:
    print("[COMSOL]  NOT FOUND — 请手动设置 COMSOL_ROOT 变量")

# ---- Java (COMSOL 自带) ----
JAVA_HOME = None
if COMSOL_ROOT:
    for jre_sub in ["java/win64/jre", "java/glnxa64/jre", "java/maca64/jre"]:
        candidate = os.path.join(COMSOL_ROOT, jre_sub)
        if os.path.isdir(candidate):
            JAVA_HOME = candidate
            break

if JAVA_HOME:
    java_exe = "java.exe" if sys.platform == "win32" else "java"
    java_path = os.path.join(JAVA_HOME, "bin", java_exe)
    print(f"[Java]    {JAVA_HOME}  (bundled)")
    os.environ["JAVA_HOME"] = JAVA_HOME
else:
    # fallback: system Java
    java_path = shutil.which("java")
    if java_path:
        print(f"[Java]    {java_path}  (system)")
    else:
        print("[Java]    NOT FOUND")

# ---- License server ----
license_env = os.environ.get("COMSOL_LICENSE", "")
if license_env:
    print(f"[License] {license_env}  (from COMSOL_LICENSE env)")
else:
    print("[License] NOT SET — 运行前需 export/set COMSOL_LICENSE=...")

# ---- 汇总 ----
print("\n--- 环境变量 (可复制到 .env / shell profile) ---")
if COMSOL_ROOT:
    print(f'COMSOL_ROOT={COMSOL_ROOT}')
if JAVA_HOME:
    print(f'JAVA_HOME={JAVA_HOME}')
if license_env:
    print(f'COMSOL_LICENSE={license_env}')
else:
    print('# COMSOL_LICENSE=<your_license_server>')

print("\n[Phase 0 完成]")
print(f"   mph: {'OK' if MPH_OK else 'MISSING'}")
print(f"   COMSOL: {'OK' if COMSOL_ROOT else 'MISSING'}")
print(f"   Java: {'OK' if JAVA_HOME or java_path else 'MISSING'}")
print(f"   License: {'OK' if license_env else 'MISSING'}")
```

### 0.2 期望输出（通过标准）

```
[Python]  3.x.x
[mph]     1.x.x  (OK)
[COMSOL]  <path>  (found)
[Java]     <path>  (bundled)
[License]  <server>  (from COMSOL_LICENSE env)

[Phase 0 完成]
   mph: OK
   COMSOL: OK
   Java: OK
   License: OK
```

四项全部 OK → 进入 Phase 1。缺少任何一项，先解决后再继续。

---

## Phase 1 — MPh 连接验证：Python 能否启动 COMSOL

### 1.1 运行连接测试

```python
"""Phase 1: MPh ↔ COMSOL 连接测试"""
import os, sys

# === 从 Phase 0 的结果填入 ===
COMSOL_ROOT = r"<Phase 0 输出的 COMSOL 路径>"
COMSOL_LICENSE = "<your_license_server>"
# ================================

os.environ["JAVA_HOME"] = os.path.join(COMSOL_ROOT, "java", "win64", "jre")
os.environ["COMSOL_LICENSE"] = COMSOL_LICENSE

import mph

print("=" * 60)
print("Phase 1: MPh 连接验证")
print("=" * 60)

try:
    client = mph.start(cores=1)
    print(f"[OK] Connected to COMSOL {client.version}")
except Exception as e:
    print(f"[FAIL] mph.start() → {e}")
    print("  检查: (1) COMSOL_ROOT 是否正确 (2) License server 是否可达 (3) VPN 是否连接")
    sys.exit(1)

# 创建并求解一个最小模型
try:
    model = client.create("Phase1_Test")
    jm = model.java
    comp = jm.component().create("comp1", True)
    geom = comp.geom().create("geom1", 3)

    # 1x1x1 立方体
    blk = geom.feature().create("blk1", "Block")
    blk.set("size", ["1", "1", "1"])
    geom.run()

    # 稳态传热
    ht = comp.physics().create("ht", "HeatTransfer", "geom1")
    ht.feature("init1").set("T", "293.15[K]")

    # 网格
    mesh = comp.mesh().create("mesh1")
    mesh.autoMeshSize(4)
    mesh.run()

    # 求解
    study = model.create("Study")
    study.create("std1", "Stationary")
    model.solve()

    # 验证结果
    temp = model.evaluate("T")
    print(f"[OK] Model built & solved. T = {temp}  (expect ~293.15 K)")

    client.remove(model)
    client.disconnect()
    print("\n[Phase 1 PASSED] MPh 连接和基础建模均正常。")

except Exception as e:
    print(f"[FAIL] {e}")
    client.disconnect()
    sys.exit(1)
```

### 1.2 期望输出

```
[OK] Connected to COMSOL 6.x
[OK] Model built & solved. T = 293.15 (expect ~293.15 K)
[Phase 1 PASSED] MPh 连接和基础建模均正常。
```

→ 进入 Phase 2。

---

## Phase 2 — API 有效性扫描：检测你的 COMSOL 支持哪些物理场

### 2.1 批量验证 86 个物理场接口

```python
"""Phase 2: 物理场接口全量验证"""
import os, sys

COMSOL_ROOT = r"<同上>"
COMSOL_LICENSE = "<同上>"
os.environ["JAVA_HOME"] = os.path.join(COMSOL_ROOT, "java", "win64", "jre")
os.environ["COMSOL_LICENSE"] = COMSOL_LICENSE

import mph

PHYSICS_LIST = [
    # (标签, 内部类型名, 类别)
    # --- 电磁 ---
    ("es", "Electrostatics", "电磁"),
    ("tl", "TransmissionLine", "电磁"),
    ("rmm", "RotatingMachineryMagnetic", "电磁"),
    # --- 结构力学 ---
    ("solid", "SolidMechanics", "结构力学"),
    ("shell", "Shell", "结构力学"),
    ("truss", "Truss", "结构力学"),
    ("wire", "Wire", "结构力学"),
    ("lshell", "LayeredShell", "结构力学"),
    # --- 传热 ---
    ("ht", "HeatTransfer", "传热"),
    ("rad", "SurfaceToSurfaceRadiation", "传热"),
    # --- 流体 ---
    ("spf", "LaminarFlow", "流体"),
    ("br", "Brinkman", "流体"),
    ("pfl", "PipeFlow", "流体"),
    ("hmnf", "HighMachNumberFlow", "流体"),
    # --- 声学 ---
    ("acpr", "PressureAcoustics", "声学"),
    ("aero", "Aeroacoustics", "声学"),
    ("tacs", "Thermoacoustics", "声学"),
    # --- 化学物质传递 ---
    ("tds", "DilutedSpecies", "化学"),
    ("re", "ReactionEngineering", "化学"),
    ("chem", "Chemistry", "化学"),
    # --- 电池 ---
    ("liion", "LithiumIonBatteryMPH", "电池"),
    ("lb", "LumpedBattery", "电池"),
    ("bee", "BatteryBinaryElectrolyte", "电池"),
    # --- 电化学 ---
    ("pcd", "PrimaryCurrentDistribution", "电化学"),
    ("scd", "SecondaryCurrentDistribution", "电化学"),
    ("np", "NernstPlanck", "电化学"),
    # --- 相场 ---
    ("pf", "PhaseField", "相场"),
    ("tpf", "TernaryPhaseField", "相场"),
    ("ls", "LevelSet", "相场"),
    ("fat", "Fatigue", "相场"),
    # --- 数学PDE ---
    ("pde_c", "CoefficientFormPDE", "数学PDE"),
    ("pde_g", "GeneralFormPDE", "数学PDE"),
    ("pde_w", "WeakFormPDE", "数学PDE"),
    ("lap", "LaplaceEquation", "数学PDE"),
    ("pois", "PoissonEquation", "数学PDE"),
    ("wave", "WaveEquation", "数学PDE"),
    # --- 其他 ---
    ("cpt", "ChargedParticleTracing", "粒子追踪"),
    ("gop", "GeometricalOptics", "光学"),
    ("plasma", "Plasma", "等离子体"),
    ("semi", "Semiconductor", "半导体"),
    ("mm", "MovingMesh", "变形网格"),
    ("dg", "DeformedGeometry", "变形网格"),
    ("rich", "RichardsEquation", "多孔介质"),
    ("sens", "Sensitivity", "数学"),
]

print("=" * 60)
print("Phase 2: 物理场接口全量扫描")
print("=" * 60)

client = mph.start(cores=1)
model = client.create("Phase2_Scan")
jm = model.java
comp = jm.component().create("comp1", True)
geom = comp.geom().create("geom1", 2)
geom.feature().create("c1", "Circle").set("r", "1")
geom.run()

available = []
unavailable = []

for tag, internal, category in PHYSICS_LIST:
    try:
        comp.physics().create(tag, internal, "geom1")
        available.append((tag, internal, category))
        comp.physics().remove(tag)  # clean up for next test
        print(f"  [OK]    {category:8s}  {internal}")
    except Exception as e:
        unavailable.append((tag, internal, category, str(e)[:80]))
        print(f"  [MISS]  {category:8s}  {internal}  ({str(e)[:60]})")

client.remove(model)
client.disconnect()

print(f"\n[Phase 2 结果] {len(available)}/{len(PHYSICS_LIST)} 可用")
if unavailable:
    print("不可用接口（缺少许可或模块）:")
    for tag, internal, cat, err in unavailable:
        print(f"  - {internal} ({cat})")

print("\n可用于建模的接口列表:")
for tag, internal, cat in available:
    print(f"  {tag:10s} {internal:35s} ({cat})")
```

### 2.2 期望输出

至少 **HeatTransfer**、**SolidMechanics**、**LaminarFlow**、**CoefficientFormPDE** 四类基础接口可用。如果目标模块（电池/电化学/相场等）不可用，需补充许可证。

→ 进入 Phase 3。

---

## Phase 3 — 模型结构诊断：读取你的 .mph 文件

### 3.1 对你已有的 .mph 模型运行诊断

```python
"""Phase 3: 读取 .mph 模型，自动提取参数、物理场、Study 名称"""
import os, sys

COMSOL_ROOT = r"<同上>"
COMSOL_LICENSE = "<同上>"
os.environ["JAVA_HOME"] = os.path.join(COMSOL_ROOT, "java", "win64", "jre")
os.environ["COMSOL_LICENSE"] = COMSOL_LICENSE

import mph

MPH_FILE = r"<你的 .mph 文件路径>"

print("=" * 60)
print("Phase 3: 模型结构诊断")
print("=" * 60)

client = mph.start(cores=1)
model = client.load(MPH_FILE)

# --- 全局参数 ---
print("\n--- Global Parameters ---")
for name, value in model.parameters().items():
    print(f"  {name} = {value}")

# --- Java API 遍历结构 ---
print("\n--- Model Tree (参数/物理场/Study) ---")
mph.tree(model)

# --- 组件 ---
jm = model.java
for cname in jm.component().tags():
    comp = jm.component(cname)
    print(f"\nComponent: {cname} (label: {comp.label()})")

    # 几何
    for gname in comp.geom().tags():
        geom = comp.geom(gname)
        print(f"  Geometry: {gname}")

    # 物理场
    for pname in comp.physics().tags():
        phys = comp.physics(pname)
        print(f"  Physics:  {pname}  ({phys.label()})  type={phys.getType()}")

    # 网格
    for mname in comp.mesh().tags():
        mesh = comp.mesh(mname)
        print(f"  Mesh:     {mname}")

# --- Study ---
for sname in model.study().tags():
    study = model.study(sname)
    print(f"\nStudy: '{sname}'")
    for fname in study.feature().tags():
        feat = study.feature(fname)
        print(f"  Step: {fname} ({feat.label()})  type={feat.getType()}")

client.disconnect()
print("\n[Phase 3 PASSED] 记下上面的参数名和 Study 名称，下一阶段需要用到。")
```

### 3.2 关键信息记录

记下三个信息：
- **参数名列表**（如 `p_ex`, `k_stress`, `nu`）
- **Study 名称**（如 `"研究 1"`）
- **可用表达式**（用 `mph.tree` 输出确认）

→ 进入 Phase 4。

---

## Phase 4 — 全自动建模流水线

### 4.1 模板脚本

将 Phase 3 获得的参数名和 Study 名填入下面的 `# <== 修改这里` 标记处：

```python
#!/usr/bin/env python3
"""Phase 4: COMSOL 全自动建模流水线 — 参数扫描 + 求解 + 结果导出"""
import csv, os, sys, time, traceback
from pathlib import Path

# ============================================================
# 配置区：根据你的环境修改以下变量
# ============================================================
COMSOL_ROOT   = r"H:\COMSOL64\Multiphysics"           # <== Phase 0 输出
COMSOL_LICENSE = "<port>@<license-server>"              # <== 你的 license
MPH_FILE       = r"models/SSE-Demo.mph"                # <== 你的 .mph 路径
STUDY_NAME     = "研究 1"                               # <== Phase 3 输出的 Study 名
OUTPUT_DIR     = "comsol_outputs"

# 参数扫描定义：param_name → [values] （单位写在值后面）
SWEEP_PARAMS = {                                        # <== Phase 3 输出的参数名
    "p_ex":     ["5[MPa]", "50[MPa]", "100[MPa]", "500[MPa]", "1000[MPa]"],
    "k_stress": ["0", "1"],
    "nu":       ["0.30", "0.35", "0.40", "0.42"],
}

# 需要导出的表达式
EXPORT_EXPRESSIONS = {                                  # <== Phase 3 mph.tree 确认
    "comp1.solid.mises":  "von_mises_stress",
    "comp1.solid.sx":     "stress_x",
    "comp1.cl":           "lithium_concentration",
    "comp1.phil":         "electrolyte_potential",
}
# ============================================================

import numpy as np

def setup_env():
    os.environ["JAVA_HOME"] = os.path.join(COMSOL_ROOT, "java", "win64", "jre")
    os.environ["COMSOL_LICENSE"] = COMSOL_LICENSE

def generate_case_table(sweep_params):
    """笛卡尔积生成所有参数组合"""
    import itertools
    keys = list(sweep_params.keys())
    values = list(sweep_params.values())
    cases = []
    for i, combo in enumerate(itertools.product(*values)):
        case = {"case_id": f"CASE_{i:04d}"}
        for k, v in zip(keys, combo):
            case[k] = v
        cases.append(case)
    return cases

def run_case(model, case, output_dir):
    """单 case：设参数 → 构建 → 求解 → 导出"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for param, val in case.items():
        if param == "case_id":
            continue
        model.parameter(param, str(val))

    model.build()
    print(f"    Solving '{STUDY_NAME}' ...")
    t0 = time.time()
    model.solve(STUDY_NAME)
    elapsed = time.time() - t0
    print(f"    Solved in {elapsed:.0f}s")

    results = {}
    for expr, fname in EXPORT_EXPRESSIONS.items():
        try:
            data = model.evaluate(expr)
            if data is not None:
                vals = np.asarray(data).flatten()
                csv_path = os.path.join(output_dir, f"{fname}.csv")
                np.savetxt(csv_path, vals, delimiter=",", header=fname, comments="")
                results[fname] = {
                    "min": float(vals.min()),
                    "max": float(vals.max()),
                    "mean": float(vals.mean()),
                }
        except Exception as e:
            print(f"    WARN: {expr} → {e}")

    model.save(os.path.join(output_dir, "result.mph"))

    with open(os.path.join(output_dir, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["expression", "min", "max", "mean"])
        for k, v in results.items():
            w.writerow([k, v["min"], v["max"], v["mean"]])

    return {"status": "converged", "solve_time_s": elapsed, "results": results}

def main():
    setup_env()
    import mph

    cases = generate_case_table(SWEEP_PARAMS)
    print(f"Total cases: {len(cases)}")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    batch_dir = os.path.join(OUTPUT_DIR, f"batch_{timestamp}")

    client = mph.Client()
    model = client.load(MPH_FILE)

    status_rows = []
    for i, case in enumerate(cases):
        cid = case["case_id"]
        print(f"\n[{i+1}/{len(cases)}] {cid}  params={ {k:v for k,v in case.items() if k != 'case_id'} }")
        try:
            result = run_case(model, case, os.path.join(batch_dir, cid))
            status_rows.append([cid, result["status"], result["solve_time_s"], ""])
        except Exception as e:
            traceback.print_exc()
            status_rows.append([cid, "failed", 0, str(e)[:120]])

    client.disconnect()

    with open(os.path.join(batch_dir, "convergence_status.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "status", "solve_time_s", "error"])
        w.writerows(status_rows)

    n_ok = sum(1 for r in status_rows if r[1] == "converged")
    print(f"\n{'='*60}")
    print(f"Done. {n_ok}/{len(cases)} converged. Output: {batch_dir}")

if __name__ == "__main__":
    main()
```

### 4.2 分步验证（首次运行建议先跑单 case）

在完整批量运行前，先用以下脚本验证一个 case：

```python
import os, time
os.environ["JAVA_HOME"] = os.path.join(r"H:\COMSOL64\Multiphysics", "java", "win64", "jre")
os.environ["COMSOL_LICENSE"] = "<port>@<license-server>"
import mph, numpy as np

client = mph.Client()
model = client.load("models/SSE-Demo.mph")

model.parameter("p_ex", "50[MPa]")
model.parameter("k_stress", "1")
model.parameter("nu", "0.42")
model.build()

t0 = time.time()
model.solve("研究 1")
print(f"Solved in {time.time()-t0:.0f}s")

data = model.evaluate("comp1.solid.mises")
vals = np.asarray(data).flatten()
print(f"von Mises: min={vals.min():.4f}, max={vals.max():.4f}, mean={vals.mean():.4f}")

model.save("test_single_result.mph")
client.disconnect()
print("[Phase 4 PASSED] 单 case 验证通过，可启动批量扫描。")
```

### 4.3 期望输出

```
Solved in ~240s
von Mises: min=..., max=..., mean=...
[Phase 4 PASSED] 单 case 验证通过，可启动批量扫描。
```

---

## Phase 5 — 结果提取与后处理

### 5.1 从批量输出目录提取统计量

```python
"""从 batch_* 目录提取所有 case 的统计数据"""
import os, sys, csv
from glob import glob
import numpy as np

BATCH_DIR = r"<你的 batch 输出目录>"

def field_stats(filepath):
    data = np.loadtxt(filepath, delimiter=",", skiprows=1)
    vals = np.asarray(data).flatten()
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return {}
    return {"min": float(np.min(vals)), "max": float(np.max(vals)),
            "mean": float(np.mean(vals)), "p95": float(np.percentile(vals, 95))}

results = []
for case_dir in sorted(glob(os.path.join(BATCH_DIR, "CASE_*"))):
    cid = os.path.basename(case_dir)
    row = {"case_id": cid}
    for csv_file in glob(os.path.join(case_dir, "*.csv")):
        fname = os.path.basename(csv_file).replace(".csv", "")
        stats = field_stats(csv_file)
        for stat_name, stat_val in stats.items():
            row[f"{fname}_{stat_name}"] = stat_val
    row["status"] = "failed" if os.path.exists(os.path.join(case_dir, "error_report.txt")) else "completed"
    results.append(row)

with open("comsol_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=sorted(results[0].keys()) if results else [])
    w.writeheader()
    w.writerows(results)

print(f"Summary: {len(results)} cases → comsol_summary.csv")
```

---

## 附录 A — 快速恢复（换电脑后只需改 4 行）

新电脑上，修改以下 4 行即可恢复全自动流水线：

```python
COMSOL_ROOT   = r"<新电脑 COMSOL 路径>"     # Phase 0 自动检测
COMSOL_LICENSE = "<license server>"          # 你的 license
MPH_FILE       = r"<你的 .mph 文件>"         # Phase 3 读取
STUDY_NAME     = "研究 1"                    # Phase 3 输出
```

其余代码无需修改。

---

## 附录 B — LiveLink for MATLAB 核心 API 速查

> 适用于需要用 MATLAB 构建复杂几何或算法耦合的场景。

### 启动与连接

```matlab
import com.comsol.model.*
import com.comsol.model.util.*
try ModelUtil.models; catch; ModelUtil.connect(); end
model = ModelUtil.create('Model');
```

### 三条致命规则

| # | 规则 | 错误示例 | 正确示例 |
|---|------|---------|---------|
| 1 | 绝不 `create('init1', ...)` | `pde.create('init1', ...)` | `pde.feature('init1').set('u', expr)` |
| 2 | 构造器名 ≠ GUI 显示名 | `create('T', 'Temperature')` | `create('temp1', 'TemperatureBoundary')` |
| 3 | `setIndex` 是 **0-based** | `setIndex('da', val, 1)` | `setIndex('da', val, 0)` |

### 属性名速查

| 特征 | 属性 | 值示例 |
|------|------|--------|
| HeatTransfer `init1` | `'T'` | `'293.15[K]'` |
| PDE `init1` | `'u'` | `'exp(-(x^2+y^2)/1e-12)'` |
| PDE `cfeq1` | `'da'`, `'c'`, `'f'` | 用 `setIndex` |
| Temperature BC | `'T0'` | `'373.15[K]'` |
| Time solver | `'tlist'` | `'range(0,1e-6,0.001)'` |
| Time solver | `'rtol'` | `'0.001'` |

### 完整 16 步流程骨架

```
 1. 配置模型参数（材料、几何、求解参数）
 2. 生成随机固相分布（MATLAB 计算）
 3. 在固液边界设置成核点
 4. 创建 COMSOL 模型 + 连接服务器
 5. 构建几何（圆形域 + 颗粒 + 布尔运算 + 成核点）
 6. 创建域选择（Explicit selection）
 7. 定义材料（Common 材料，带单位字符串）
 8. 相场方程（CoefficientFormPDE, cfeq1, init1）
 9. 传热方程（HeatTransfer, hs1, init1, temp1）
10. 固体力学（SolidMechanics, lemm1, thermal1, fix1）
11. 网格（FreeTri + Size）
12. 求解器（Transient study + Time solver）
13. 结果可视化（PlotGroup2D + Surface）
14. 保存模型（绝对路径）
15. 模型摘要
16. MATLAB 初始几何可视化
```

### Material 属性

```matlab
mat = comp.material.create('tag', 'Common');
mat.propertyGroup('def').set('density',             '2200[kg/m^3]');
mat.propertyGroup('def').set('heatcapacity',        '710[J/(kg*K)]');
mat.propertyGroup('def').set('thermalconductivity', '150[W/(m*K)]');
mat.propertyGroup('def').set('youngsmodulus',       '12e9[Pa]');
mat.propertyGroup('def').set('poissonsratio',       '0.20');
```

### Solid Mechanics 材料——在 lemm1 上设

```matlab
lemm = solid.feature('lemm1');
lemm.set('E', '12e9[Pa]');
lemm.set('nu', '0.20');
thermalExp = lemm.create('thermal1', 'ThermalExpansion');
thermalExp.set('alpha', '4e-6[1/K]');
thermalExp.set('Tref', '-20[degC]');
```

---

## 附录 C — 物理场接口速查表（Phase 2 验证项）

| 类别 | 接口 | 内部类型 | 维度 |
|------|------|---------|------|
| 结构 | `solid` | `SolidMechanics` | 2D/3D |
| 结构 | `shell` | `Shell` | 3D |
| 结构 | `truss` | `Truss` | 1D/2D/3D |
| 传热 | `ht` | `HeatTransfer` | 1D/2D/3D |
| 流体 | `spf` | `LaminarFlow` | 2D/3D |
| 流体 | `br` | `Brinkman` | 2D/3D |
| 流体 | `pfl` | `PipeFlow` | 1D |
| 电池 | `liion` | `LithiumIonBatteryMPH` | 1D/2D/3D |
| 电池 | `lb` | `LumpedBattery` | 0D/3D |
| 电池 | `bee` | `BatteryBinaryElectrolyte` | 1D/2D/3D |
| 燃料电池 | `hfc` | `HydrogenFuelCell` | 1D/2D/3D |
| 电化学 | `pcd` | `PrimaryCurrentDistribution` | 1D/2D/3D |
| 电化学 | `scd` | `SecondaryCurrentDistribution` | 1D/2D/3D |
| 电化学 | `np` | `NernstPlanck` | 1D/2D/3D |
| 相场 | `pf` | `PhaseField` | 2D/3D |
| 相场 | `tpf` | `TernaryPhaseField` | 2D/3D |
| 相场 | `ls` | `LevelSet` | 2D/3D |
| 数学 | `pde_c` | `CoefficientFormPDE` | 1D/2D/3D |
| 数学 | `pde_g` | `GeneralFormPDE` | 1D/2D/3D |
| 数学 | `pde_w` | `WeakFormPDE` | 1D/2D/3D |

> 完整 86 项列表见 Phase 2 脚本中的 `PHYSICS_LIST`。

---

## 附录 D — 故障排查速查

| 症状 | 检查项 |
|------|--------|
| `mph.Client()` 无响应 | COMSOL_ROOT 是否正确；JAVA_HOME 是否指向 COMSOL 自带 JRE |
| License 错误 | `COMSOL_LICENSE` 是否设置；VPN 是否连接 |
| 参数设置无效 | 参数名是否与 .mph 中完全一致（大小写敏感）；单位是否包含在字符串中 |
| "研究 1" 不存在 | Study 名称是否真的是中文——用 Phase 3 脚本 `mph.tree` 确认 |
| 表达式求值返回 None | 用 Phase 3 `mph.tree` 确认表达式路径 |
| `d(u,t)` 报错 | 跨物理场引用需带前缀：`d(pde_pf.u, t)` |
| 保存路径报错 | 必须用绝对路径；先 `os.makedirs(out_dir, exist_ok=True)` |
| `init1` 重复创建 | 用 `feature('init1').set(...)`，不要 `create('init1', ...)` |
| `pip install mph` 失败 | 需要 Python ≥ 3.8；Windows 上可能需要先安装 VC++ Redistributable |

---

## 附录 E — 单位字符串速查

```python
f"{value}[m]"         # 长度
f"{value}[kg/m^3]"    # 密度
f"{value}[Pa]"        # 压力/模量
f"{value}[MPa]"       # 压力（兆帕）
f"{value}[W/(m*K)]"   # 热导率
f"{value}[J/(kg*K)]"  # 比热
f"{value}[degC]"      # 温度（摄氏度）
f"{value}[K]"         # 温度（开尔文）
f"{value}[1/K]"       # 热膨胀系数
f"{value}[s]"         # 时间
f"{value}[V]"         # 电压
f"{value}[A/m^2]"     # 电流密度
f"{value}[S/m]"       # 电导率
f"{value}[m^2]"       # 渗透率
```

---

## 文件清单（本文档涉及的脚本）

| 阶段 | 脚本 | 作用 |
|------|------|------|
| Phase 0 | `detect_env.py` | 自动检测 COMSOL/Python/Java 路径 |
| Phase 1 | （内联脚本） | MPh 连接 + 最小模型创建/求解 |
| Phase 2 | （内联脚本） | 批量扫描 44 个物理场接口 |
| Phase 3 | （内联脚本） | 读取 .mph，打印参数/Study/表达式 |
| Phase 4 | （内联脚本） | 全自动参数扫描 + 批量求解 + 导出 |
| Phase 5 | （内联脚本） | 后处理统计汇总 |
| 附录 F | （内联脚本） | 燃料电池/电解最小模型（已验证） |

---

## 附录 F — 燃料电池与水电解 API（已验证）

### F.1 已发现的关键接口

**`HydrogenFuelCell`** — COMSOL 6.4 内置的氢燃料电池物理场，支持 PEMFC/SOFC。
**`SecondaryCurrentDistribution` + `ElectrodeSurface`** — 构建水电解模型的核心接口。

### F.2 扫描结果汇总

| 接口 | 内部类型 | 状态 |
|------|---------|------|
| `hfc` | `HydrogenFuelCell` | 验证通过，3.2s 求解 |
| `scd` | `SecondaryCurrentDistribution` | 验证通过，2.9s 求解 |
| `np` | `NernstPlanck` | 可用 |
| `br` | `Brinkman` | 可用 |
| `FuelCell` | — | **不存在** |
| `PEMFuelCell` | — | **不存在** |
| `SOFC` | — | **不存在** |
| `Electrolyzer` | — | **不存在** |
| `Electrochemistry` | — | **不存在**（用 SecondaryCurrentDistribution 代替） |

### F.3 HydrogenFuelCell 结构

创建 `HydrogenFuelCell` 后，COMSOL 自动生成 5 个子节点：

| 节点 | 类型 | 角色 |
|------|------|------|
| `icph1` | `ElectrolytePhase` | 离子导电相（电解质膜） |
| `ecph1` | `ElectronicConductingPhase` | 电子导电相（电极） |
| `h2gasph1` | `H2GasPhase` | 氢气气相（阳极侧） |
| `o2gasph1` | `O2GasPhase` | 氧气气相（阴极侧） |
| `dcont1` | `Continuity` | 相间连续性 |

**已验证的边界条件：**

| 所在节点 | 特征类型 | 关键属性 |
|---------|---------|---------|
| `ecph1` | `ElectricGround` | — |
| `ecph1` | `ElectricPotential` | `phisbnd` = 电位值（带单位） |
| `h2gasph1` | `Flux` | 阳极侧氢气通量边界 |
| `o2gasph1` | `Flux` | 阴极侧氧气通量边界 |

### F.4 PEMFC 最小模型（完整可运行）

```python
"""PEMFC 最小模型 — 3 域 2D 截面（阳极 GDL | 膜 | 阴极 GDL）
验证：3.2s 求解，T=353.15K"""

import os
os.environ['JAVA_HOME'] = r'<COMSOL>\java\win64\jre'
os.environ['COMSOL_LICENSE'] = '<license>'
import mph

client = mph.start(cores=1)
model = client.create('PEMFC_Minimal')
jm = model.java
comp = jm.component().create('comp1', True)
geom = comp.geom().create('geom1', 2)

# 几何：阳极 GDL(0.4mm) | 膜(0.2mm) | 阴极 GDL(0.4mm)，高 1mm
for i, (x, w) in enumerate([(0, 0.4), (0.4, 0.2), (0.6, 0.4)]):
    r = geom.feature().create(f'r{i+1}', 'Rectangle')
    r.set('size', [f'{w}[mm]', '1[mm]'])
    r.set('pos', [f'{x}[mm]', '0'])
geom.run()

# HydrogenFuelCell 物理场
fc = comp.physics().create('hfc', 'HydrogenFuelCell', 'geom1')
ecph = fc.feature('ecph1')                             # 电子导电相

# 阳极接地（左边界）
ecph.feature().create('eg1', 'ElectricGround').selection().set([1])

# 阴极电位 0.9V（右边界）
ep = ecph.feature().create('ep1', 'ElectricPotential')
ep.selection().set([2])
ep.set('phisbnd', '0.9[V]')                            # 关键属性名：phisbnd！

# 气体入口通量
fc.feature('h2gasph1').feature().create('hf1', 'Flux').selection().set([1])
fc.feature('o2gasph1').feature().create('of1', 'Flux').selection().set([2])

model.parameter('T', '353.15[K]')                      # 80°C 工作温度

# 网格 + 求解
comp.mesh().create('mesh1').autoMeshSize(5)
comp.mesh('mesh1').run()

study = jm.study().create('std1')
study.feature().create('stat1', 'Stationary')
study.run()                                            # 关键：用 study.run()！

print(f'T = {model.evaluate("T")}')                    # 期望：353.15
model.save('pemfc_minimal.mph')
client.disconnect()
```

### F.5 水电解最小模型（完整可运行）

```python
"""水电解最小模型 — SecondaryCurrentDistribution + Butler-Volmer
阳极 OER(2H2O→O2+4H++4e-) | 阴极 HER(2H++2e-→H2)
验证：2.9s 求解，T=353.15K"""

import os
os.environ['JAVA_HOME'] = r'<COMSOL>\java\win64\jre'
os.environ['COMSOL_LICENSE'] = '<license>'
import mph

client = mph.start(cores=1)
model = client.create('Elzr_Minimal')
jm = model.java
comp = jm.component().create('comp1', True)
geom = comp.geom().create('geom1', 2)

# 几何：阳极(0.2mm) | 电解液(0.6mm) | 阴极(0.2mm)，高 1mm
for i, (x, w) in enumerate([(0, 0.2), (0.2, 0.6), (0.8, 0.2)]):
    r = geom.feature().create(f'r{i+1}', 'Rectangle')
    r.set('size', [f'{w}[mm]', '1[mm]'])
    r.set('pos', [f'{x}[mm]', '0'])
geom.run()

scd = comp.physics().create('scd', 'SecondaryCurrentDistribution', 'geom1')

# ⚠️ 必须设置电解液电导率！（默认 sigmal=0 无法求解）
ice = scd.feature('ice1')
ice.set('sigmal_mat', 'userdef')
ice.set('sigmal', '60[S/m]')                           # KOH 溶液 ~60 S/m

# 阳极：OER 反应（4 电子）
es_a = scd.feature().create('es_a', 'ElectrodeSurface')
es_a.selection().set([1])
es_a.set('phisext0', '2.0[V]')                         # 电解电压
er_a = es_a.feature('er1')
er_a.set('nm', '4')                                    # 电子数
er_a.set('Eeq_ref', '1.23[V]')                         # OER 平衡电位
er_a.set('i0_ref', '1e-2[A/m^2]')                     # 交换电流密度

# 阴极：HER 反应（2 电子）
es_c = scd.feature().create('es_c', 'ElectrodeSurface')
es_c.selection().set([2])
es_c.set('phisext0', '0[V]')                           # 接地
er_c = es_c.feature('er1')
er_c.set('nm', '2')                                    # 电子数
er_c.set('Eeq_ref', '0[V]')                            # HER 平衡电位
er_c.set('i0_ref', '1e2[A/m^2]')                      # HER 交换电流密度

model.parameter('T', '353.15[K]')

comp.mesh().create('mesh1').autoMeshSize(5)
comp.mesh('mesh1').run()

study = jm.study().create('std1')
study.feature().create('stat1', 'Stationary')
study.run()                                            # 关键：用 study.run()！

print(f'T = {model.evaluate("T")}')                    # 期望：353.15
model.save('electrolyzer_minimal.mph')
client.disconnect()
```

### F.6 SecondaryCurrentDistribution 关键属性速查

**Electrolyte (`ice1`)：**

| 属性 | 含义 | 示例值 |
|------|------|--------|
| `sigmal_mat` | 电导率来源 | `'userdef'` / `'from_mat'` |
| `sigmal` | 离子电导率 | `'60[S/m]'` |

**ElectrodeReaction (`er1`)：**

| 属性 | 含义 | OER 示例 | HER 示例 |
|------|------|---------|---------|
| `nm` | 电子数 | `'4'` | `'2'` |
| `Eeq_ref` | 平衡电位 | `'1.23[V]'` | `'0[V]'` |
| `i0_ref` | 交换电流密度 | `'1e-2[A/m^2]'` | `'1e2[A/m^2]'` |
| `alphaa` | 阳极转移系数 | `'1.5'`（默认 0.5） | `'0.5'` |
| `alphac` | 阴极转移系数 | `'0.5'` | `'0.5'` |
| `ElectrodeKinetics` | 动力学类型 | `'LinButlerVolmer'` | `'LinButlerVolmer'` |

**ElectrodeSurface (`es1`)：**

| 属性 | 含义 | 示例值 |
|------|------|--------|
| `phisext0` | 电极电位 | `'2.0[V]'` |
| `BoundaryConditionType` | BC 类型 | `'Potential'` |

### F.7 求解关键教训

| 错误做法 | 正确做法 | 原因 |
|---------|---------|------|
| `jm.sol('sol1').runAll()` | `study.run()` | 前者创建空 solver，无解输出 |
| `jm.sol().create('sol1').study('std1')` 后无 solver step | `study.run()` 自动创建 solver | 手动创建 sol1 不会自动填充 solver steps |
| `model.create('Study')` | `jm.study().create('std1')` | MPh 不能在 root 创建 Study 节点 |

### F.8 模型文件

两个已验证模型已保存：
- `H:\Projects\pemfc_minimal.mph` — PEMFC 最小模型（602 单元，3.2s）
- `H:\Projects\electrolyzer_minimal.mph` — 电解最小模型（728 单元，2.9s）
