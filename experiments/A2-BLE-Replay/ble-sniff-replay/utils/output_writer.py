import json
from utils.logger import logger_setup
import os
logger = logger_setup(__name__)


def write_json(data, output_filepath: str = "output/att_parsed_output.json"):
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    with open(output_filepath, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Parsed {len(data)} entries saved to {output_filepath}")
