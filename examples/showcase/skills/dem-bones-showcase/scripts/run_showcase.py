"""Bounded showcase entry point."""

# Import third-party modules
from dcc_mcp_core.skill import skill_entry


@skill_entry
def run_showcase(output_dir, case_name="tentacle"):
    # Import standard library modules
    import importlib
    from pathlib import Path

    # Import third-party modules
    import unreal_case

    importlib.reload(unreal_case)
    report = unreal_case.run(output_dir, case_name=case_name)
    if case_name == "arm":
        # Import third-party modules
        import unreal_skin

        root = Path(unreal_skin.__file__).parent
        report["skin_preview"] = unreal_skin.setup(
            root / "materials" / "skin", root / "assets" / "lighting" / "studio_small_09_2k.hdr"
        )
    return {"success": True, "context": report}
