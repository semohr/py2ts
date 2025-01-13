try:
    import typer
except ImportError:
    raise ImportError(
        "Please install package with cli dependencies: pip install git+https://github.com/semohr/py2ts.git[cli]"
    )


cli = typer.Typer(
    name="py2ts",
    help="Convert Python data structures to TypeScript types.",
)


@cli.command()
def main():
    typer.echo("Hello World")
