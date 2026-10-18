# Conditional COMSOL workflows / 条件式 COMSOL 工作流

This fork includes the user's modeling guide and Shishvan 2021 reproduction
experience as full-text references. At initialization, the MCP server supplies
48 execution points **and their activation conditions** to the client. This works
with the regular `python -m src.server` and `comsol-mcp` entry points, including
stdio and HTTP transports; no workstation-specific launcher is required.

## Activation comes first / 先判断唤起条件

Agents must identify the current task and record the applicable rule groups
before changing a model. A COMSOL or electrochemistry task alone does **not**
activate the Shishvan workflow.

| Workflow | Activate only when |
|---|---|
| Environment, API, units and delivery | Relevant COMSOL operations; reuse valid environment checks for read-only tasks |
| Full Phase 0–5 automation and sweeps | First end-to-end setup or an explicitly requested pipeline/parameter sweep |
| Particle/nucleation/phase-field/thermal/mechanical template | The task actually includes that coupled system or explicitly requests the template |
| Hydrogen fuel cells | The target model uses or needs `HydrogenFuelCell` |
| Water electrolysis | The corresponding reaction system uses `SecondaryCurrentDistribution` and `ElectrodeSurface`; example OER/HER parameters are system-specific |
| Shishvan constitutive law and geometry | Explicit reproduction of Shishvan, Fleck & Deshpande, JPS 488 (2021), 229437, or its specified Li/LLZO stripping model |
| Four-stage continuation | That model is active and its CreepRamp/MechCouple/RampFactor sequence is being built, solved or diagnosed |
| Nonlocal Ztip iteration | That model is active and nonlocal dislocation-density/impedance self-consistency is required |
| MATLAB LiveLink | The actual execution path uses MATLAB; existing custom solvers must be verified before `runAll()` |
| Paper-specific postprocessing | Reproducing that paper's plots, void-nucleation criterion or project checkpoints |
| Electrothermal calibration and runtime lessons | Standalone HeatTransfer startup, solution/dataset maintenance, pulse-switch integration, temperature-input tracing, or explicitly requested P2D thermal/DC-temperature/constant-power calibration and component reduction; use the per-item gates in the reference |

The Chinese execution checklist contains the complete conditions and all 48
points. Paper parameters, solver scales, tolerances, geometry and historical
diagnostic values are never defaults for unrelated models. Historical successful
solves do not establish final self-consistency or completion of the paper reproduction.

## Read the full references

| `docs_get(topic)` | MCP resource |
|---|---|
| `user_execution_rules` | `comsol://workflow/user_execution_rules` |
| `user_modeling_reference` | `comsol://workflow/user_modeling_reference` |
| `user_shishvan2021_log` | `comsol://workflow/user_shishvan2021_log` |
| `electrothermal_calibration` | `comsol://workflow/electrothermal_calibration` |

Documents are bundled under `src/knowledge/user_workflows/` and work without
PDF embedding dependencies or a vector index. The source documents retain
historical examples and caveats; example license servers are replaced with
placeholders for publication. Verify paths, COMSOL API types, dimensions, units,
license availability and actual model selections on the current installation.

The electrothermal reference also covers unsolved temperature fields still
supplied by active couplings, model-input override scope, authorized component
reduction, surface-specific versus whole-cell resistance, actual integration
steps at pulse switches, dependent initialization/storage solutions, and
cascading dataset removal. These are conditional diagnostics, not automatic
model rewrites or universal solver settings. Pulse verification includes the
switching window; representative initial-state checks are distinguished from
full protocol replay. Research data and calibrated parameter values are not
included in this guidance.

## Optional local documents and environment

The following environment variables replace individual bundled documents with
local UTF-8 Markdown files. Use absolute paths. Missing files fail at startup.
Restart the MCP process after changing rules so initialization instructions are
refreshed; `docs_get` and resource reads return the current file content.

```text
COMSOL_MCP_EXECUTION_RULES=/absolute/path/execution_rules.md
COMSOL_MCP_MODELING_REFERENCE=/absolute/path/modeling_reference.md
COMSOL_MCP_SHISHVAN_LOG=/absolute/path/shishvan2021_log.md
COMSOL_MCP_ELECTROTHERMAL_REFERENCE=/absolute/path/electrothermal_calibration.md
```

The existing `COMSOL_MCP_VERSION` selects an installed COMSOL version.
`COMSOL_MCP_CORES` optionally limits the number of cores for stdio pre-start;
unset values preserve the upstream default. Set `JAVA_HOME` to the current
installation's bundled JRE if needed. No COMSOL installation path, remote
license server or version is hard-coded in this integration. A failed stdio
pre-start now exits with a clear error instead of advertising an unusable backend.

For Codex, point an MCP stdio entry at the environment's Python executable,
with `args = ["-m", "src.server"]`, a `cwd` pointing to this repository and
a startup timeout suitable for COMSOL initialization. Other MCP clients can
use the same entry point described in the main README.

## Validation

`python -m unittest tests.test_user_workflow` checks initialization instructions,
conditional activation boundaries, full-text retrieval, resource registration
and configurable document paths without requiring COMSOL or a JVM.

On the original workstation, the local integration also passed a real COMSOL
6.4 stdio test: model creation, cube geometry, mesh, a stationary PDE with known
solution `u=1`, result evaluation and MPH saving. Maximum absolute error was
`1.78e-14`. This is evidence for that workstation's basic chain, not a guarantee
for other licenses/modules or a claim that Shishvan reproduction is complete.

## Runtime fixes from electrothermal modeling

- Standalone MPh can load an OSGi SLF4J binder that breaks HeatTransfer's
  ASHRAE/SQLite initialization. The JVM-start context expands only the standalone
  `plugins/*` classpath and omits `org.osgi.slf4j.*` binders. It preserves all
  other JARs and restores the JPype function after startup, even on error.
  Set `COMSOL_MCP_STANDALONE_SLF4J=off` to disable; remote `apiplugins/*` is
  untouched. Restart the MCP process for classpath changes to take effect.
- Result tools resolve the actual default dataset before MPh 1.4's
  `inner`/`outer` calls and map `first`/`last`/`end` to actual numeric indices.
  Numeric inner selections are passed as lists as required by MPh. Use explicit
  dataset names when multiple study stages exist. Global evaluation rejects
  multiple/non-finite values instead of silently returning the first time point.
- `solution_update(solution_name)` refreshes an explicit existing solution after
  postprocessing operators are added. It never re-solves changed physics; call
  the appropriate solver after changes to parameters, physics, geometry or mesh.
- `model_save` rejects explicit format/extension conflicts. Use `.mph` for
  binary snapshots and `format='Java'` with `.java` for Java source exports.
- The electrothermal reference documents conditional lessons on protected
  parameters, zero-resistance limits, double-counted heat, circular constant-power
  commands, nonlocal Jacobian memory, pulse-edge energy integration and validation
  boundaries. It contains no private calibration data or fitted values.

Run the focused regressions and a real backend test with the MCP Python:

```bash
python -m pytest tests -q
python scripts/check_runtime.py --output /absolute/path/runtime-check --version 6.4
```

The real check uses a new disposable model: it initializes HeatTransfer,
solves a transient PDE with known final value, checks multi-value rejection and
numeric final-index selection, updates a solution, exports MPH/Java, then reloads
the MPH and checks the final time. It writes logs and a report outside the repo;
it does not load or alter research models. It requires a valid COMSOL license,
the HeatTransfer interface and access to COMSOL's user recovery directory.
