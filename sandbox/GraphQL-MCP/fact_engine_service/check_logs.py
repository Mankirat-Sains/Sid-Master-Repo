#!/usr/bin/env python3
"""Quick script to verify logging is working"""
import logging
import sys

# Test logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True
)

logger = logging.getLogger("test")
logger.info("=" * 80)
logger.info("TEST: This is an INFO level log message")
logger.info("=" * 80)
logger.warning("TEST: This is a WARNING level log message")
logger.error("TEST: This is an ERROR level log message")
logger.debug("TEST: This is a DEBUG level log message (you might not see this)")

print("\n✅ If you see the messages above, logging is working!")
print("   If you don't see them, check your terminal output settings.\n")


