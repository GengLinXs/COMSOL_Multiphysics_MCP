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

Documents are bundled under `src/knowledge/user_workflows/` and work without
PDF embedding dependencies or a vector index. The source documents retain
historical examples and caveats; example license servers are replaced with
placeholders for publication. Verify paths, COMSOL API types, dimensions, units,
license availability and actual model selections on the current installation.

## Optional local documents and environment

The following environment variables replace individual bundled documents with
local UTF-8 Markdown files. Use absolute paths. Missing files fail at startup.
Restart the MCP process after changing rules so initialization instructions are
refreshed; `docs_get` and resource reads return the current file content.

```text
COMSOL_MCP_EXECUTION_RULES=/absolute/path/execution_rules.md
COMSOL_MCP_MODELING_REFERENCE=/absolute/path/modeling_reference.md
COMSOL_MCP_SHISHVAN_LOG=/absolute/path/shishvan2021_log.md
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
