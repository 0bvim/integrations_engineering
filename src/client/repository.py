import os
import json
from typing import Dict, List, Any
from loguru import logger

from src.config import DATA_INBOUND_DIR, DATA_OUTBOUND_DIR

class ClientRepository:
    """Repository for interacting with the client's file system"""

    def __init__(self, inbound_dir: str = DATA_INBOUND_DIR, outbound_dir: str = DATA_OUTBOUND_DIR):
        self.inbound_dir = inbound_dir
        self.outbound_dir = outbound_dir

    async def get_inbound_workorders(self) -> List[Dict[str, Any]]:
        """Read all inbound workorder files"""
        workorders = []

        try:
            files = [f for f in os.listdir(self.inbound_dir) if f.endswith(".json")]

            for file_name in files:
                file_path = os.path.join(self.inbound_dir, file_name)
                try:
                    with open(file_path, "r") as f:
                        workorder = json.load(f)
                        if self._validate_inbound_workorder(workorder):
                            workorders.append(workorder)
                        else:
                            logger.warning(f"Invalid workorder format in {file_name}")
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.error(f"Error parsing JSON from {file_name}: {e}")
                except IOError as e:
                    logger.error(f"IO error reading {file_name}: {e}")
        except Exception as e:
            logger.error(f"Error reading inbound directory: {e}")

        return workorders

    def _validate_inbound_workorder(self, workorder: Dict[str, Any]) -> bool:
        """Validate that the inbound workorder has required fields and valid orderNo"""
        required_fields = ["orderNo", "isCanceled", "isDeleted", "creationDate"]
        for field in required_fields:
            if field not in workorder:
                return False
        order_no = workorder.get("orderNo")
        if not isinstance(order_no, int):
            return False
        return True

    async def write_outbound_workorder(self, workorder: Dict[str, Any]) -> bool:
        """Write a workorder to the outbound directory"""
        try:
            if "orderNo" not in workorder:
                logger.error("Cannot write workorder without orderNo")
                return False

            file_path = os.path.join(self.outbound_dir, f"{workorder['orderNo']}.json")

            with open(file_path, "w") as f:
                json.dump(workorder, f, default=str)

            logger.info(f"Wrote outbound workorder to {file_path}")
            return True
        except IOError as e:
            logger.error(f"IO error writing workorder {workorder.get('orderNo', 'unknown')}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error writing outbound workorder: {e}")
            return False
