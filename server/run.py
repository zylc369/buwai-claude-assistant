#!/usr/bin/env python3
"""Run FastAPI server using configuration from application.yml."""

import uvicorn
from config import get_config


def main() -> None:
    config = get_config()
    uvicorn.run(
        "app:app",
        host=config.server.host,
        port=config.server.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
