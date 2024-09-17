import uasyncio as asyncio

#import asyncio
import time

async def waitabit(ack_event, timout):
    try:
        await asyncio.wait_for(ack_event.wait(), timout)
    except asyncio.TimeoutError:
        pass
    
    return ack_event.is_set()
   
async def tx():
    print("tx started")

    ack_event = asyncio.Event()
    
    print("tx waiting ...", ack_event.is_set())
    
    start_time = time.time()
#    ack_event.set()
    result = await waitabit(ack_event,3)
    end_time = time.time()
    
    print("tx waited", result, end_time-start_time)
    
    for i in range(2):
        ans=input("Block test " + str(i) + " " )
    
    print("tx ended", ans)
    
async def rx(arg):
    print("rx started", arg)
    await asyncio.sleep(1)
    print("RX finished")
    
async def main():
#    tx_task=asyncio.create_task(tx())
#    rx_task=asyncio.create_task(rx(2))
    batch = asyncio.gather(tx(), rx(1))
    print("Awaiting batch")
    await batch
#    await tx_task
#    await rx_task
 
    asyncio.sleep(10)
    print("main finishing...")

asyncio.run(main())

    
    
    