"""Project data generation.

This module contains definitions and builders for Project entities.
"""

import random
from datetime import timedelta

from ..constants import RNG_SEED
from .helpers import iso, now, uid

_RNG = random.Random(RNG_SEED)


# ═══════════════════ Project Definitions ═══════════════════

_PROJECT_DEFS = [
    {
        "id": "proj-code-agent-v2",
        "name": "Code Agent v2",
        "description": "Code generation and repair agent training",
        "owner": "algo-team",
        "tags": {"team": "agent-rl", "domain": "code"},
    },
    {
        "id": "proj-reasoning",
        "name": "Reasoning Model",
        "description": "Multi-step reasoning and problem solving agent",
        "owner": "reasoning-team",
        "tags": {"team": "reasoning", "domain": "reasoning"},
    },
]


def build_projects():
    # type: () -> List[Dict]
    """Build project records from definitions.

    Returns:
        List of project dictionaries with timestamps
    """
    _now_ts = now()
    projects = []  # type: List[Dict]
    for pd in _PROJECT_DEFS:
        projects.append(
            {
                "id": pd["id"],
                "name": pd["name"],
                "description": pd["description"],
                "owner": pd["owner"],
                "tags": pd["tags"],
                "created_at": iso(_now_ts - timedelta(days=30)),
                "updated_at": iso(_now_ts),
            }
        )
    return projects


def add_project(projects, data):
    # type: (List[Dict], Dict) -> Dict
    """Add a new project to the list.

    Args:
        projects: The list of existing projects
        data: The project data to add

    Returns:
        The newly created project
    """
    proj = {
        "id": uid("proj", data.get("name", ""), str(len(projects))),
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "owner": data.get("owner", ""),
        "tags": data.get("tags", {}),
        "created_at": iso(now()),
        "updated_at": iso(now()),
    }
    projects.append(proj)
    return proj


def get_project_defs():
    # type: () -> List[Dict]
    """Get the raw project definitions.

    Returns:
        List of project definition dictionaries
    """
    return _PROJECT_DEFS
