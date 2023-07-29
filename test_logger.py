import logger

logger.info("Hello", "World")
logger.warn("The", "quick", "brown", "fox")
logger.error("Long Message", "Short Message")
logger.debug("X")

print("-"*80)

for line in logger.iterate():
    print(line)

logger.clear()
