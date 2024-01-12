from __future__ import annotations

import argparse
from pathlib import Path

from sqlmodel import Session

from letters.anagrammer.database import engine
from letters.config.insertdictionary import (
    LadderAdder,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load ladders from a file.")
    parser.add_argument("path", type=str, help="Path to the file to load.")
    args = parser.parse_args()

    with Session(engine) as session:
        LadderAdder(session=session).insert_from_files(Path(args.path))
