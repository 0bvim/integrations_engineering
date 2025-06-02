"""Entrypoint for the TracOS ↔ Client Integration Flow"""
import asyncio
import os
import signal
from loguru import logger
from dotenv import load_dotenv

from src.utils.logging import setup_logging
from src.tracos.repository import TracOSRepository
from src.client.repository import ClientRepository
from src.translation.mapper import WorkorderMapper

# Setup signal handling for graceful shutdown
shutdown_event = asyncio.Event()

class IntegrationService:
    """Main service that orchestrates the integration flow"""

    def __init__(self, tracos_repo: TracOSRepository = None, client_repo: ClientRepository = None, mapper: WorkorderMapper = None):
        self.tracos_repo = tracos_repo or TracOSRepository()
        self.client_repo = client_repo or ClientRepository()
        self.mapper = mapper or WorkorderMapper()

    async def process_inbound(self):
        """Process the inbound flow (Client → TracOS)"""
        logger.info("Starting inbound processing...")

        # Get all workorders from client files
        inbound_workorders = await self.client_repo.get_inbound_workorders()
        logger.info(f"Found {len(inbound_workorders)} inbound workorders to process")

        for client_workorder in inbound_workorders:
            try:
                tracos_workorder = self.mapper.client_to_tracos(client_workorder)

                success = await self.tracos_repo.create_or_update_workorder(tracos_workorder)

                if not success:
                    logger.error(f"Failed to save workorder {client_workorder.get('orderNo', 'unknown')}")
            except Exception as e:
                logger.error(f"Error processing inbound workorder: {e}")

        logger.info("Inbound processing complete")

    async def process_outbound(self):
        """Process the outbound flow (TracOS → Client)"""
        logger.info("Starting outbound processing...")

        # Get all unsynchronized workorders from TracOS
        workorders = await self.tracos_repo.get_unsynchronized_workorders()
        logger.info(f"Found {len(workorders)} outbound workorders to process")

        # Process each workorder
        for tracos_workorder in workorders:
            try:
                client_workorder = self.mapper.tracos_to_client(tracos_workorder)

                success = await self.client_repo.write_outbound_workorder(client_workorder)

                if success:
                    await self.tracos_repo.mark_as_synced(str(tracos_workorder["_id"]))
                else:
                    logger.error(f"Failed to write outbound workorder {tracos_workorder.get('number', 'unknown')}")
            except Exception as e:
                logger.error(f"Error processing outbound workorder: {e}")

        logger.info("Outbound processing complete")

    async def run_once(self):
        """Run the integration flow once"""
        try:
            await self.tracos_repo.connect()
            # Process inbound first, then outbound
            await self.process_inbound()
            await self.process_outbound()
        except Exception as e:
            logger.error(f"Error running integration flow: {e}")
        finally:
            await self.tracos_repo.disconnect()

    async def run_continuously(self, interval_seconds=60):
        """Run the integration flow continuously with a specified interval"""
        logger.info(f"Starting continuous integration flow (interval: {interval_seconds}s)")

        try:
            while not shutdown_event.is_set():
                await self.run_once()
                try:
                    await asyncio.wait_for(
                        shutdown_event.wait(),
                        timeout=interval_seconds
                    )
                except asyncio.TimeoutError:
                    pass
        finally:
            logger.info("Integration service shutting down")

async def main():
    load_dotenv()
    setup_logging()

    def handle_signal(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        shutdown_event.set()

    loop = asyncio.get_event_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal, sig, None)

    # Log startup message
    logger.info("Starting TracOS ↔ Client Integration Flow")
    logger.info(f"Using inbound directory: {os.environ.get('DATA_INBOUND_DIR', './data/inbound')}")
    logger.info(f"Using outbound directory: {os.environ.get('DATA_OUTBOUND_DIR', './data/outbound')}")
    logger.info(f"Using MongoDB URI: {os.environ.get('MONGO_URI', 'mongodb://localhost:27017/tractian')}")

    # Create and run the integration service
    try:
        service = IntegrationService()
        await service.tracos_repo.connect()
    except Exception:
        logger.error("Failed to connect to TracOS repository")
        exit(1)

    if os.getenv("RUN_MODE", "once") == "continuous":
        interval = int(os.getenv("SYNC_INTERVAL_SECONDS", "60"))
        await service.run_continuously(interval)
    else:
        await service.run_once()

    logger.info("Integration flow completed")

if __name__ == "__main__":
    asyncio.run(main())
