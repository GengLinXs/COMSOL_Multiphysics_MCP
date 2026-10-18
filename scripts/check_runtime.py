"""Real stdio/HeatTransfer/transient-result regression check. Requires COMSOL.

Run with the MCP environment's Python; outputs stay outside the repository:
  python scripts/check_runtime.py --output /absolute/path/check --version 6.4
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile

import anyio
import numpy as np
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def check(args):
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output).resolve() if args.output else Path(tempfile.mkdtemp(prefix="comsol-mcp-check-"))
    output.mkdir(parents=True, exist_ok=True)
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "checks": [], "success": False}
    environment = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", COMSOL_MCP_CORES="1", COMSOL_MCP_TRANSPORT="stdio")
    if args.version:
        environment["COMSOL_MCP_VERSION"] = args.version
    params = StdioServerParameters(command=sys.executable, args=["-m", "src.server"], cwd=str(root), env=environment)
    try:
        with (output / "server.log").open("w", encoding="utf-8") as log:
            with anyio.fail_after(300):
                async with stdio_client(params, errlog=log) as (read, write):
                    async with ClientSession(read, write) as session:
                        initialization = await session.initialize()
                        assert "electrothermal_calibration" in initialization.instructions
                        report["tools"] = len((await session.list_tools()).tools)

                        async def call(tool, expected_success=True, **arguments):
                            result = await session.call_tool(tool, arguments)
                            assert not result.isError, result
                            data = result.structuredContent
                            if data is None:
                                data = json.loads(next(block.text for block in result.content if block.type == "text"))
                            assert data.get("success", True) == expected_success, data
                            report["checks"].append({"tool": tool, "expected_success": expected_success})
                            print(tool, "OK", flush=True)
                            return data

                        report["session"] = await call("comsol_status")
                        await call("docs_get", topic="electrothermal_calibration")
                        await call("model_create", name="MCP_Runtime_Regression")
                        await call("model_create_component", space_dimension=2)
                        await call("geometry_add_rectangle", geometry_name="comp1_geom", size=[1, 1])
                        await call("geometry_build", geometry_name="comp1_geom")
                        heat = await call("physics_add_heat_transfer")
                        await call("physics_remove", physics_name=heat["physics"]["name"])
                        # du/dt + u = t + 1, u(0)=0; exact solution u=t (t in seconds).
                        await call("physics_add_coefficient_form_pde", equation_properties={"c": "1", "a": "1", "f": "t/1[s]+1", "da": "1[s]"})
                        await call("mesh_create")
                        await call("study_create", study_type="TimeDependent", study_name="runtime", step_properties={"tlist": "range(0,0.1,1)"})
                        await call("study_solve", study_name="runtime")
                        await call("results_global_evaluate", expected_success=False, expression="t")
                        final = await call("results_global_evaluate", expression="t", unit="s", inner="last")
                        assert abs(final["value"] - 1) < 1e-12
                        field = await call("results_evaluate", expression="u", inner="end")
                        values = np.asarray(field["value"], dtype=float)
                        assert values.size and np.isfinite(values).all()
                        report["transient_max_error"] = float(np.max(np.abs(values - 1)))
                        assert report["transient_max_error"] < 1e-3
                        solutions = await call("solutions_list")
                        await call("solution_update", solution_name=solutions["solutions"][-1])
                        await call("model_save", expected_success=False, file_path=str(output / "wrong.java"), format="Comsol")
                        await call("model_save", file_path=str(output / "runtime.mph"), format="Comsol")
                        await call("model_save", file_path=str(output / "runtime.java"), format="Java")
                        assert not (output / "wrong.java").exists()
                        assert "class " in (output / "runtime.java").read_text(encoding="utf-8")
                        await call("model_load", file_path=str(output / "runtime.mph"))
                        reloaded = await call("results_global_evaluate", expression="t", unit="s", inner="last")
                        assert abs(reloaded["value"] - 1) < 1e-12
                        report["success"] = True
    except BaseException as error:
        report["error"] = repr(error)
        raise
    finally:
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report: {output / 'report.json'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    parser.add_argument("--version")
    options = parser.parse_args()
    anyio.run(check, options)
