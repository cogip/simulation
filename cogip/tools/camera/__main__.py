#!/usr/bin/env python3
import logging
from typing import Annotated

import typer

from . import logger
from .info import cmd_info


app = typer.Typer()
app.command(name="info")(cmd_info)


@app.callback()
def common(
    ctx: typer.Context,
    debug: Annotated[bool, typer.Option(
        "-d", "--debug",
        help="Turn on debug messages",
        envvar=["COGIP_DEBUG", "CAMERA_DEBUG"],
    )] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)
        obj = ctx.ensure_object(dict)
        obj["debug"] = True


def main():
    """
    Launch COGIP Camera Tools.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-camera` script using this function as entrypoint.
    """
    app()


if __name__ == '__main__':
    main()
