"""Portable user workflow instructions and full-text reference resources.

Documents are reference material, not blanket instructions to run every workflow.
The activation table in execution_rules.md determines which rules apply.
"""

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .embedded import KNOWLEDGE_FILES

WORKFLOW_DIR = Path(__file__).parent / "user_workflows"
DOCUMENTS = {
    "user_execution_rules": ("execution_rules.md", "COMSOL MCP 基本执行点", "COMSOL_MCP_EXECUTION_RULES"),
    "user_modeling_reference": ("modeling_reference.md", "COMSOL 自动建模指南（完整参考）", "COMSOL_MCP_MODELING_REFERENCE"),
    "user_shishvan2021_log": ("shishvan2021_log.md", "Shishvan 2021 工作日志（文献专用）", "COMSOL_MCP_SHISHVAN_LOG"),
    "electrothermal_calibration": ("electrothermal_calibration.md", "电热标定与独立 MPh 运行经验（按条件唤起）", "COMSOL_MCP_ELECTROTHERMAL_REFERENCE"),
}


def document_path(topic: str) -> Path:
    filename, _, variable = DOCUMENTS[topic]
    override = os.environ.get(variable)
    return Path(override).expanduser().resolve() if override else WORKFLOW_DIR / filename


def workflow_instructions() -> str:
    """Read the current rules at startup and state their activation boundary."""
    rules = document_path("user_execution_rules").read_text(encoding="utf-8")
    return (
        "COMSOL 条件式工作要求：首先阅读下方“唤起条件与适用边界”，"
        "记录本次任务激活的规则组和依据，只执行适用部分。"
        "燃料电池、水电解、相场模板、Shishvan 本构/四阶段求解/Ztip 外循环"
        "以及 MATLAB LiveLink 均须满足各自唤起条件，不能作为其他模型的默认流程。"
        "历史成功、示例数值及待确认事项不代表当前验证结果。"
        "完整来源可通过 docs_get(user_modeling_reference)、"
        "docs_get(user_shishvan2021_log) 或 comsol://workflow/<topic> 读取。\n\n"
        + rules
        + "\n\n新增条件式经验：实际独立 MPh/HeatTransfer 运行错误、末端解选择/解刷新、"
        "导出审计，或明确开展电池 P2D 电热标定/温度内阻/恒功率耦合时，"
        "读取 docs_get('electrothermal_calibration') 或 comsol://workflow/electrothermal_calibration，"
        "先依据其中唤起条件选择适用条目；不为其他任务套用标定参数、nojac 或电路改写。"
    )


def register_workflow_resources(mcp: FastMCP) -> None:
    """Expose the same live documents through docs_get and MCP resources."""
    def register(topic: str, title: str) -> None:
        path = document_path(topic)
        path.read_text(encoding="utf-8")  # Catch missing overrides before serving requests.
        KNOWLEDGE_FILES[topic] = {
            "file": str(path.resolve()),
            "title": title,
            "description": "条件式工作依据；先核对唤起条件，完整参考不等于全部启用。",
            "keywords": ["workflow", "COMSOL", "Shishvan", "唤起条件", "执行点"],
        }

        @mcp.resource(f"comsol://workflow/{topic}", name=title, mime_type="text/markdown")
        def read_document() -> str:
            return path.read_text(encoding="utf-8")

    for topic, (_, title, _) in DOCUMENTS.items():
        register(topic, title)
