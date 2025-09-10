import logging
import sys

def setup_logging():
    """Sets up a structured logger that outputs to the console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    # In a production environment, you might add a file handler
    # or a handler for a log management service.
    logging.info("Logging configured.")
