"""Shared utilities for QGIS Python Console scripts in the Ulmer Schachtel project.

Provides robust repository path resolution and helper functions for managing
layer groups and removing duplicate layers.
"""

from pathlib import Path
from qgis.core import QgsProject


def get_repo_paths(project: QgsProject) -> tuple[Path, Path, Path, Path]:
    """Finds and returns the paths for the repository.

    Returns:
        tuple[Path, Path, Path, Path]: (repo_dir, data_dir, raster_dir, styles_dir)
    """
    if not project.fileName():
        print("  ⚠ Projekt nicht gespeichert — erst speichern, dann erneut ausführen.")
        raise SystemExit("Projekt nicht gespeichert.")

    project_file = Path(project.fileName())
    repo_dir = next(
        (p for p in [project_file.parent] + list(project_file.parents) if (p / "data" / "processed").is_dir()),
        None
    )
    if not repo_dir:
        print(f"  ⚠ Repository-Stammverzeichnis nicht gefunden (ausgehend von {project_file}).")
        raise SystemExit("Repository-Stammverzeichnis nicht gefunden.")

    return (
        repo_dir,
        repo_dir / "data" / "processed",
        repo_dir / "data" / "raster",
        repo_dir / "qgis" / "styles",
    )


def remove_layers_by_name(project: QgsProject, name: str) -> None:
    """Removes all layers with the given name from the project."""
    for dup in project.mapLayersByName(name):
        project.removeMapLayer(dup.id())


def get_or_create_group(
    project: QgsProject,
    name: str,
    insert_before: str | None = None,
    insert_after: str | None = None,
):
    """Finds or creates a layer group, placing it relative to existing groups.

    Args:
        project: The QgsProject instance.
        name: The name of the group to find or create.
        insert_before: Optional name of group to insert before.
        insert_after: Optional name of group to insert after (takes precedence if before not found).
    """
    root = project.layerTreeRoot()
    old = root.findGroup(name)
    if old:
        root.removeChildNode(old)

    insert_idx = len(root.children())
    if insert_before:
        anchor = root.findGroup(insert_before)
        if anchor:
            insert_idx = root.children().index(anchor)
    elif insert_after:
        anchor = root.findGroup(insert_after)
        if anchor:
            insert_idx = root.children().index(anchor) + 1
        else:
            insert_idx = 0

    return root.insertGroup(insert_idx, name)


def set_multiply_blend_mode(layer) -> None:
    """Sets the blend mode of the layer to Multiply, compatible with QGIS 3 (PyQt5) and QGIS 4 (PyQt6)."""
    from qgis.PyQt.QtGui import QPainter

    # Try PyQt6 style first
    try:
        layer.setBlendMode(QPainter.CompositionMode.CompositionMode_Multiply)
        return
    except (AttributeError, TypeError):
        pass

    # Try PyQt5 style
    try:
        layer.setBlendMode(QPainter.CompositionMode_Multiply)
        return
    except (AttributeError, TypeError):
        pass

    # Fallback to integer (for other cases)
    try:
        layer.setBlendMode(13)
        return
    except (AttributeError, TypeError) as e:
        print(f"  ⚠ Konnte Blend-Mode 'Multiply' nicht setzen: {e}")
