"""Limit the standalone OSGi logging workaround to JVM startup, not the install."""

from contextlib import contextmanager
import logging
import os
from pathlib import Path
from threading import RLock

import jpype

logger = logging.getLogger(__name__)
_startup_lock = RLock()


def standalone_classpath(classpath):
    """Expand MPh's plugins wildcard, excluding only the OSGi SLF4J binder.

    COMSOL 6.4 HeatTransfer/ASHRAE SQLite can load this binder outside OSGi
    and fail in SLF4JLoggerFactory. Remote apiplugins and explicit lists are
    left alone. The installation and all other logging/API jars are untouched.
    """
    if not isinstance(classpath, (str, os.PathLike)):
        return classpath
    path = Path(classpath)
    if path.name != "*" or path.parent.name.lower() != "plugins":
        return classpath
    jars = sorted(path.parent.glob("*.jar"))
    excluded = [p for p in jars if p.name.startswith("org.osgi.slf4j.")]
    if not excluded:
        return classpath
    logger.info("Standalone JVM: excluding OSGi SLF4J binders: %s", [p.name for p in excluded])
    return [str(p) for p in jars if p not in excluded]


@contextmanager
def standalone_jvm_compatibility():
    """Temporarily adapt the actual classpath MPh passes to JPype.

    Set COMSOL_MCP_STANDALONE_SLF4J=off to use the original classpath.
    JVM classpaths cannot be repaired after startup; use a fresh process.
    """
    with _startup_lock:
        if os.environ.get("COMSOL_MCP_STANDALONE_SLF4J", "auto").lower() == "off" or jpype.isJVMStarted():
            yield
            return
        original = jpype.startJVM

        def start_jvm(*args, **kwargs):
            if "classpath" in kwargs:
                kwargs["classpath"] = standalone_classpath(kwargs["classpath"])
            return original(*args, **kwargs)

        jpype.startJVM = start_jvm
        try:
            yield
        finally:
            jpype.startJVM = original
