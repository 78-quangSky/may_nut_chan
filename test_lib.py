key = ['M1', 'M0', 'Y4', 'M170', 'M3', 'TS4', 'M799']
value = [chr(97+i) for i in range(len(key))]
print(value)

dict_status_addr = dict(zip(key, value))
# print(dict_status_addr['M1'])

class DictAsAttributes:
    """A class that converts a dictionary to attributes.
    
    Args:
        list_key (list): A list of keys of the dictionary.
        
    Returns:
        None
    
    Note: All attributes are lowercase and set in alphabetical order (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p,...).
    Example:
        >>> list_key = ['M1', 'M0', 'Y4', 'M170', 'M3', 'TS4', 'M799']
        >>> dict_status_addr = DictAsAttributes(list_key)
        >>> dict_status_addr.m1
        'a'
        >>> dict_status_addr.m0
        'b'
    """
    def __init__(self, list_key):
        list_value = [chr(97+i) for i in range(len(list_key))]
        dictionary = dict(zip(list_key, list_value))
        self.__dict__['_data'] = dictionary

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            raise AttributeError(f"'DictAsAttributes' object has no attribute '{name}'")

# Variables to store initial states
class init:
    On = 1                          # Initiate on state
    Run = 1                         # Initiate running state
    Idle = 1                        # Initiate idle state
    Alarm = 1                       # Initiate alarm state
    Setup = 1                       # Initiate setup state
    Off = 1                         # Initiate off state
    Ready = 1                       # Initiate ready state

print(init.On)
init.On = 2

from datetime import datetime, timedelta
import time
old_operationTime = datetime.now()
offset_operationTime = 3600.67675
time.sleep(5)
new_operationTime = datetime.now()
delta_operationTime = (new_operationTime - old_operationTime + timedelta(seconds=offset_operationTime)).total_seconds()
_delta_operationTime = (datetime.fromtimestamp(delta_operationTime) + timedelta(hours=-7)).strftime('%H:%M:%S')
print(delta_operationTime)
print(_delta_operationTime)

import asyncio

async def looper():
    for i in range(1_000_000_000):
        print(f'Printing {i}')
        await asyncio.sleep(0.5)

async def main():
    print('Starting')
    future = asyncio.ensure_future(looper())

    print('Waiting for a few seconds')
    await asyncio.sleep(4)

    print('Cancelling')
    future.cancel()

    print('Waiting again for a few seconds')
    await asyncio.sleep(2)

    print('Done')

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())