# COMSOL MCP 基本执行点

适用范围：本工作区通过 COMSOL MCP、MPh、Java API 或 MATLAB LiveLink 执行的 COMSOL 工作。来源为用户指定的 `modeling_reference.md` 和 `shishvan2021_log.md`；按下表唤起相关部分并读取对应原文，完整原文可检索但不表示其中所有流程均已激活。以下为操作检查表；示例路径、许可服务器和旧域编号必须现场核实，不能照抄。

## 唤起条件与适用边界（先判断，再执行）

开始任务先在工作记录中声明本次触发了哪些规则组及证据（用户目标、模型文件/物理场或指定文献）；未触发的专用流程保持不启用。仅使用 COMSOL、非线性求解或电化学这些宽泛关键词，不足以唤起 Shishvan 专用流程。

| 规则组 | 明确唤起条件 | 不满足条件时 |
|---|---|---|
| 通用环境与 API（1–10、12、16 的适用部分） | 进行任意 COMSOL 操作；首次环境/版本变化时重做连接与最小求解，已有证据可复用 | 无需为每次只读查询重建模型、全量扫描接口或执行完整六阶段 |
| Phase 0–5、参数扫描与导出（1、15–16） | 新环境首次打通完整自动建模链路，或用户明确要求完整流水线/参数扫描/批量计算 | 仅执行当前任务必要阶段；单次模型检查不启动扫描，已有模型无需重建几何 |
| 多物理场 16 步模板（11） | 用户任务包含随机颗粒、固液界面成核和相场/传热/固体力学耦合，或明确采用指南附录 B 模板 | 不生成随机颗粒、成核点，也不额外添加 PDE、传热、力学接口；普通耦合只借鉴相关顺序 |
| 燃料电池（13） | 建立/检查氢燃料电池模型，且实际使用或拟使用 HydrogenFuelCell | 不自动添加燃料电池接口、气相通量或示例电位 |
| 水电解（14） | 建立/检查相应电极反应模型，且实际使用 SecondaryCurrentDistribution/ElectrodeSurface；OER/HER 示例仅限对应体系 | 不给任意电化学模型强加 60 S/m、OER/HER、电子数或参考电位 |
| Shishvan 2021 理论、本构和几何（17–26） | 用户明确要求 Shishvan–Fleck–Deshpande 2021 JPS 229437 复现，或明确指定其 Li/LLZO 剥离、半球杂质、幂律蠕变与应力修正界面电流模型 | 不使用其材料数值、400a 几何、稳态假设或“不需要相场/移动网格”的结论限制其他问题 |
| Shishvan 四阶段求解（27–32） | 上一项已触发，且当前任务建立、恢复、求解或诊断这套 CreepRamp/MechCouple/RampFactor 连续序列（如 SSE-rebuild11） | 不为其他模型强制创建四阶段、Fully Coupled、指定缩放或关闭稳定化；仅借鉴核实单位/初值/边界的通用诊断原则 |
| Shishvan 非局部 Ztip 外循环（33–41） | 已触发该文献模型，并明确需要其位错密度非局部平均和自洽界面阻抗，或处理对应 ztip_iteration.m | 不引入 Ztip、位错密度、对数割线、1e-4 阈值或论文诊断数值；其他外循环按各自方程和容差 |
| MATLAB LiveLink 专用 API（39–40，以及8–12中相应 MATLAB 语法） | 当前执行路径实际使用 MATLAB LiveLink；四阶段 runAll 还必须满足对应模型已存在有效定制求解序列 | Python/MCP 工作不自动启动 MATLAB；新模型按实际 Study 生成求解器 |
| Shishvan 论文后处理与恢复（42–47） | 继续该论文复现、定量对图、验证其空洞萌生判据，或恢复所列项目版本 | 不对其他模型要求这些特定指标、文件名或认定其研究状态 |
| 通用交付（48） | 交付任意 COMSOL 操作结果 | 只报告本次实际操作和已激活规则，不把历史结果当作本次结果 |

规则中“必须”“优先”“禁止”等表述均受该组唤起条件约束。若模型已明显偏离原文，先记录适用性与新假设，再决定保留哪些专用规则。不得仅凭旧文件名或含糊关键词断言研究目标；可先只读检查模型，仍不清楚再询问。数值、求解尺度、算法阈值和历史参考输出均不是跨任务默认值。

## 一、分阶段执行与环境

1. 严格按 Phase 0 环境检测 → Phase 1 连接和最小求解 → Phase 2 接口验证 → Phase 3 模型诊断 → Phase 4 单工况后批量 → Phase 5 后处理推进，每阶段记录证据；失败先修复。
2. 检测实际 Python（非 Microsoft Store）、MPh、COMSOL 安装路径、COMSOL 自带 Java、有效许可证。优先使用 COMSOL 自带 JRE。许可可来自本地安装配置或许可服务器；环境变量未设置不等于无有效许可。服务器许可需检查网络/VPN，禁止把原文示例服务器当作本机配置。
3. 连接失败先检查环境及 MCP 安装，再进行真实启动、创建模型、网格、求解、结果验证；仅 MCP 握手不代表 COMSOL 可用。
4. 按目标维度验证实际接口与许可，区分接口名错误、维度不支持和缺少模块。原指南称 86 项，但 Phase 2 实际列表为 44 项；以真实测试数量为准。
5. 加载已有模型后，先提取完整树、全局参数、组件、几何、域/边界选择、物理场内部类型、网格、Study 标签与显示名、求解器和数据集。区分树中节点与实际可求值表达式；表达式还须实际求值验证。
6. 使用绝对路径保存，先建目录；保护原模型和已收敛基准，另存版本并记录时间、源文件、参数、单位、求解耗时、状态与错误。

## 二、API 与建模规范

7. 使用 `model.java` 属性，不调用 `model.java()`。按现场版本查询内部类型与合法属性，GUI 显示名不等于构造器名。
8. 修改自动生成的 `init1`，不要重复创建。`setIndex` 从 0 开始。跨物理场变量/时间导数使用实际前缀，如 `d(pde_pf.u,t)`。
9. 参数名大小写、Study 名称和表达式必须以模型为准；所有有量纲输入带单位，材料通过 Common/propertyGroup 正确设置；固体力学 E、nu 和热膨胀还需核实 lemm1/thermal1 的来源设置。
10. 新模型使用 `jm.study().create(...)` 与 `study.run()` 生成有效求解序列；不要在 MPh 根节点创建 Study，也不要仅创建空 `sol1` 就运行。已有定制四阶段模型使用实际已验证的 `model.sol('sol1').runAll()`，不得被默认 Study 重建覆盖。
11. 复杂耦合遵循参数 → 颗粒/成核点 → 模型连接 → 几何和布尔运算 → 显式/命名域选择 → 材料 → PDE → 传热 → 力学和耦合 → 网格 → Study/solver → 可视化 → 绝对路径保存 → 摘要及初始几何验证的完整链条，按实际任务采用。
12. 原文的传热/PDE/力学、时间步和材料属性速查全部保留为参考；以本机合法属性为准，不能混用不同物理接口的 Temperature/TemperatureBoundary 等类型。
13. 燃料电池使用已验证的 `HydrogenFuelCell`（icph1、ecph1、h2gasph1、o2gasph1、dcont1），电子电位属性为 `phisbnd`，气相通量在对应气相节点；不要虚构 FuelCell、PEMFuelCell、SOFC 内部类型。
14. 水电解使用 `SecondaryCurrentDistribution` + `ElectrodeSurface`；ice1 设置 `sigmal_mat=userdef` 和实际非零 `sigmal`。ElectrodeSurface 用 `phisext0`/BoundaryConditionType，er1 用 nm、Eeq_ref、i0_ref、alphaa、alphac、ElectrodeKinetics。原文 OER/HER 电子数、参考电位及交换电流仅作对应示例，不当作任意体系通用参数。不要使用虚构的 Electrolyzer/Electrochemistry 接口。
15. 验证完整参数组合之前先运行一个代表性工况。每个 case 单独保存场数据、MPH、summary、收敛状态、耗时和错误；失败可继续其他独立工况，但不得把失败/缺失导出标成成功。
16. 后处理统计 min/max/mean/p95，识别并报告 NaN/Inf/空数据；过滤非有限值时保留异常数量。普通节点平均不等于物理体积/面积平均。汇总不同工况用字段并集，避免只采用第一行字段或把 summary.csv 误作场数据。

## 三、Shishvan 2021 专用物理检查

17. 研究对象是 Li/LLZO 剥离、二维轴对称稳态空洞萌生条件；未显式追踪空洞生长，不擅自添加相场/移动网格。参考 Shishvan、Fleck、Deshpande，JPS 488 (2021) 229437。
18. 原文 R=L=H=400a；a=0.25 μm 对应 R=L=H=100 μm，lambda=0.5 μm。四分之一圆圆心在轴线与界面交点。旧 L=400 μm、R=200 μm、0.1 μm 间隙是测试几何。存在间隙时必须映射跨边界变量。求解成功不证明几何已忠实复现。
19. 核对完整参数表：kap=0.046 S/m、G_Li=3 GPa、b0=0.25 nm、V_Li=13.1e-6 m³/mol、Omv=6e-6 m³/mol、hv=50 kJ/mol、sigma0=1 MPa、edot0=0.01 s⁻¹、edotc=1e-5 s⁻¹、n=6.6、sigmac≈0.351119 MPa、Z0=5 Ω·cm²、beta=0.5、alphak=2.7、lam=0.5 μm。当前 323 K 与论文室温存在待核实差别；COMSOL/MATLAB 温度必须一致。
20. 使用当前已验证的 `edot_eff=spf.sr/sqrt(3)`、`sigmac=sigma0*(edotc/edot0)^(1/n)`、`mu_eff=(sigma0/(3*edot0))*(max(edot_eff,edotc)/edot0)^(1/n-1)`。禁止回退到历史错误 `n-1` 指数；与论文印刷记法的严格对应仍须单独核实。
21. 如采用平滑 `edot_reg=0.5*(edot_eff+edotc+sqrt((edot_eff-edotc)^2+(0.02*edotc)^2))`，记录平滑参数，黏度和等效应力同步，使用 `sig_vm=3*mu_eff*edot_eff`。
22. 电解质仅需要 Laplace 电势：CoefficientFormPDE、phi_e 单位 V、c=kap，其余不必要系数为零；底部 phi_e=0，外侧绝缘，接触面电化学通量，杂质无通量。域 1 仅为历史编号，实际重新核实；不要带入旧 cd/liion 的额外状态变量。
23. Li 使用不可压缩轴对称 Creeping Flow、自定义黏度、无旋流时关闭周向自由度，优先 P2/P1。历史 Li 域 2 需现场确认。
24. 平直接触界面 `v·n=j*V_Li/F` 且零切向牵引；杂质表面无穿透且零切向牵引，不误用默认无滑移；Li 顶部/外侧施加外压法向牵引、零切向牵引并允许进出。
25. 统一使用 `jloc=(phip-phi_e-MechCouple*sig_nn*V_Li/F_const)/Zloc` 同时驱动 PDE 通量和 SPF 法向速度。`sig_nn=-p+spf.K_stress_tensorzz` 必须核实是否为总应力、压力是否重复计算；核查节点法向通量和速度正负号。
26. `Zloc=Ztip+(Z0-Ztip)*(1-exp(-max(r-a_def,0[m])/lam))`，只作用于正确接触边界，防止域外外推。`phip=RampFactor*jinf*(L_el/kap+Z0)` 中 L_el 必须等于实际厚度。有限堆压与电流独立加载，检查低 RampFactor 时机械修正主导的情况。

## 四、连续求解与故障诊断

27. 四阶段：初始化 → CreepRamp 0→1（`mu_eff=(1-CreepRamp)*mu_lin+CreepRamp*mu_full`）→ MechCouple 0→1 → RampFactor 0.01→1；最终三个参数均为 1。
28. 显式核实每阶段待求解变量初值、未求解变量来源、solution tag、参数索引和数据集：2 继承 1 最终解；3 继承 2 的 CreepRamp=1；4 继承 3 的 MechCouple=1 且 RampFactor=0.01；扫描逐点继承前一收敛解。不得错误继承 RampFactor=1 的历史存储解。
29. 保留各阶段日志。第三阶段 Fully Coupled 曾验证成功，第四阶段优先沿用成功配置，以保存 MPH 为准。求解器串联不会自动保证正确继承。
30. 手动尺度参考 phi_e=0.01 V、u2/w2=1e-9 m/s、p=1e6 Pa，并核查实际日志“缩放因变量”，防止电势/速度尺度填反。
31. P2/P1 Stokes 遇 spf.tauNSViscTerm、tau_m、streamlinens 除零时检查并关闭不需要的 Streamline/Crosswind/Isotropic Diffusion。逐点单向约束不一致时检查边界重叠、入口/轴线/杂质/Open Boundary 与不适用的 Suppress backflow。
32. NaN/Inf 先查本构正则化、阻抗外推、边界和符号；Newton 振荡先查尺度与初值加载。任何阶段失败优先查继承，再调整连续步长、阻尼、网格；不得把早期失败直接认定为不存在物理解。

## 五、非局部阻抗自洽与 MATLAB

33. 外循环：Ztip → COMSOL → 应力 → 位错密度 → 非局部积分 → Ztip_raw。rho_d 在 sigma>=sigmac 时为 `k*((sigma-sigmac)/(G*b))^2`，否则 0；当前 k=1、alphak=2.7，改变 k 时避免重复计入。
34. 积分区域严格按杂质 a 与 lambda 定义。二维轴对称 mphint2 使用 `intvolume=on`；分子/分母单位必须 `{'m','m^3'}`，不是 `{'1/m','m^3'}`。rho_avg 单位 m⁻²，转 μm⁻²乘 1e-12。
35. 每轮检查 V_lambda>0、实际返回单位、非负密度与 `rho_avg<=rho_max`。原错误 372973.568 μm⁻² 应为约 0.372974 μm⁻²，不能高于最大 2.248 μm⁻²。
36. 参考诊断（并非本次测试结果）：Ztip=Z0=5 Ω·cm²、RampFactor=1、T=323 K 时，V_lambda=3.57462748e-19 m³、max sigma=1.475655 MPa、rho_max=2.248143 μm⁻²、rho_avg=0.372974 μm⁻²、有效空位分数=1.45626639e-7、Ztip_raw=1.187134 Ω·cm²；几何/工况改变后不可强行匹配。
37. 按原文有效空位与阻抗公式计算：theta_hat=exp(-hv/(R*T))+(alphak*V_Li*b^2/Omv)*rho_avg；Ztip_raw=Z0*theta_hat^(beta-1)*exp(-(1-beta)*hv/(R*T))，注意量纲与合并参数约定。
38. 固定欠松弛与相对步长上限可作为回退；优先采用 `g=log(Ztip_raw/Ztip)` 的自适应对数割线、历史点预测、信赖步长与 COMSOL 失败回退。保持 Ztip 正值，记录每轮 Ztip/Ztip_raw/rho_avg/真实残差，不仅看更新步长。
39. 普通 MATLAB 先用 mphstartcomsolmphserver 启动服务，再 mphstart(port)，不要连接不存在的服务器。有量纲参数 mphevaluate 指定目标单位；无量纲 alphak/beta 直接读取，不误把 'value' 当单位。
40. 对已定制四阶段执行 `model.sol('sol1').runAll()`；后处理选最终数据集并用 solnum=end、outersolnum=end，核实最终 RampFactor=1，避免读到其他阶段。
41. 只有 `abs(Ztip_raw-Ztip)/Ztip<1e-4` 且当前场确为当前 Ztip 的成功解，才标记最终自洽。不得先更新参数再保存旧场冒充新解；不达容差的保存为 checkpoint。

## 六、后处理、交付与状态

42. 输出 jloc/jinf 对 r/a_def（远场接近 1）、K_J=max(j)/jinf、standard/modified BV 比较；sig_vm/sigma0；rho_d*1e-12 的最大值、非局部平均和距离分布；Zloc/[ohm*cm²] 对 r/a_def，尖端接近 Ztip、远场回到 Z0。
43. 用 Li 总应力计算杂质表面法向牵引，按轴对称半球面积平均（理想面积 2*pi*a²），明确法向与拉压符号；对照原文 Eq.3.5 验证，再用堆压扫描确定空洞萌生临界值。
44. 论文定量图之前验证：电流守恒、远场电流、杂质无穿透、反应电流与速度一致、积分域/单位/均值一致、网格无关性（尖端应力/rho_avg/Ztip/K_J）、外循环自洽与参数敏感性。
45. 恢复顺序：核实 SSE-rebuild11 基础模型及 Ztip=Z0 完整求解 → 核实四阶段继承 → MATLAB 单次诊断 → Ztip 外循环 → 确认残差与参数/场一致 → 论文后处理。
46. 区分早期 SSE-Ver01、SSE-rebuild-test、当前 SSE-rebuild11、ztip_iteration.m、checkpoint 和预定最终 SSE-rebuild11-ztip；核对实际路径与时间戳，不覆盖基准。
47. 历史已解决：本构、基本重建、双向耦合、连续求解与继承、LiveLink、积分单位、外循环基本算法。仍待确认：最终自洽 Ztip、严格几何/温度、网格无关性、牵引及临界空洞结果、论文图定量一致性。不能把历史局部成功报告为完整复现完成。
48. 每次交付列出实际修改、参数和单位、执行阶段、求解/自洽证据、数据集、输出绝对路径、未解决问题；保留两份源文档的完整内容，不因清单压缩丢失参考细节。
