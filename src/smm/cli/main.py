import click

from smm.cli.init_cmd import init
from smm.cli.import_cmd import import_docs
from smm.cli.search_cmd import search_cmd as do_search
from smm.cli.serve_cmd import serve
from smm.cli.mcp_cmd import mcp
from smm.cli.status_cmd import status, stop
from smm.cli.skill_cmd import skill


@click.group()
@click.version_option(version="0.1.0", prog_name="smm")
def cli() -> None:
    """SMM — seekdb Markdown MCP. Index local documents into seekdb with MCP service."""
    pass


cli.add_command(init)
cli.add_command(import_docs)
cli.add_command(do_search)
cli.add_command(serve)
cli.add_command(mcp)
cli.add_command(status)
cli.add_command(stop)
cli.add_command(skill)


if __name__ == "__main__":
    cli()
