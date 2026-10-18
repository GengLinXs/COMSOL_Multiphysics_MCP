"""Verify workflow delivery and activation boundaries without a COMSOL license."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import anyio
from mcp.server.fastmcp import FastMCP

from src.knowledge.embedded import get_docs, KNOWLEDGE_FILES
from src.knowledge.user_workflow import (
    DOCUMENTS, document_path, register_workflow_resources, workflow_instructions,
)


class TestUserWorkflow(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ)
        self.environment.start()
        for _, _, variable in DOCUMENTS.values():
            os.environ.pop(variable, None)
        self.knowledge = patch.dict(KNOWLEDGE_FILES)
        self.knowledge.start()

    def tearDown(self):
        self.knowledge.stop()
        self.environment.stop()

    def test_instructions_include_activation_boundaries(self):
        instructions = workflow_instructions()
        for text in ["唤起条件与适用边界", "48.", "不为其他模型强制创建四阶段",
                     "仅使用 COMSOL", "不引入 Ztip", "MATLAB LiveLink"]:
            self.assertIn(text, instructions)
        from src.server import mcp
        self.assertIn("唤起条件与适用边界", mcp.instructions)

    def test_docs_and_resources_deliver_all_reference_text(self):
        mcp = FastMCP("workflow-test")
        register_workflow_resources(mcp)

        async def check():
            resources = await mcp.list_resources()
            self.assertEqual(len(resources), len(DOCUMENTS))
            for topic in DOCUMENTS:
                expected = document_path(topic).read_text(encoding="utf-8")
                docs = get_docs(topic)
                self.assertTrue(docs["success"])
                self.assertEqual(docs["content"], expected)
                resource = list(await mcp.read_resource(f"comsol://workflow/{topic}"))
                self.assertEqual(resource[0].content, expected)
        anyio.run(check)

    def test_local_override_refresh_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules.md"
            path.write_text("# Local conditional rules", encoding="utf-8")
            os.environ["COMSOL_MCP_EXECUTION_RULES"] = str(path)
            self.assertIn("# Local conditional rules", workflow_instructions())
            mcp = FastMCP("override-test")
            register_workflow_resources(mcp)
            path.write_text("# Updated local rules", encoding="utf-8")
            self.assertEqual(get_docs("user_execution_rules")["content"], "# Updated local rules")
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                workflow_instructions()


if __name__ == "__main__":
    unittest.main()
