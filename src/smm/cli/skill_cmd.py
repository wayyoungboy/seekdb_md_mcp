from __future__ import annotations

import os
import shutil
import subprocess

import click

from smm.core.config import SMM_DIR


@click.command()
@click.option("--install", "-i", is_flag=True, help="Install skill to Claude Code")
@click.option("--uninstall", "-u", is_flag=True, help="Uninstall skill from Claude Code")
def skill(install: bool, uninstall: bool) -> None:
    """Manage Claude Code skill installation."""
    if install and uninstall:
        click.echo("Use --install or --uninstall, not both.")
        return

    if install:
        _install_skill()
    elif uninstall:
        _uninstall_skill()
    else:
        click.echo("Usage: smm skill --install  or  smm skill --uninstall")


def _install_skill() -> None:
    skill_dir = SMM_DIR / "skill"
    skill_file = skill_dir / "SKILL.md"
    skill_src = _find_skill_source()

    if skill_src is None:
        click.echo("Error: Could not find SKILL.md in the smm package.")
        return

    skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(skill_src, skill_file)
    click.echo(f"Skill installed to: {skill_file}")
    click.echo("\nAdd to your Claude Code config:")
    click.echo(f'  "skills": ["{skill_file}"]')


def _uninstall_skill() -> None:
    skill_file = SMM_DIR / "skill" / "SKILL.md"
    if skill_file.exists():
        skill_file.unlink()
        click.echo(f"Skill removed from: {skill_file}")
    else:
        click.echo("Skill not installed.")


def _find_skill_source() -> str | None:
    from smm import __file__ as smm_init
    if smm_init:
        candidate = os.path.join(os.path.dirname(smm_init), "skill", "SKILL.md")
        if os.path.exists(candidate):
            return candidate
    return None
