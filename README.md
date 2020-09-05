# Evently [![Build Status](https://travis-ci.com/dboslee/evently.svg?branch=master)](https://travis-ci.com/dboslee/evently)

A lightweight event bus for python asyncio
<br></br>

**About Evently**:
- Written in python3.8
- Built around asynio
- Uses type hinting
- Simple API
- Threadsafe 
<br></br>
### How to install
`pip install evently`
<br></br>
### Code Examples<br></br>
Here is a complete example
```
import asyncio
from evently import Evently, Event

loop = asyncio.get_event_loop()
evently = Evently(loop)


@evently.subscribe("hello")
async def say_world(event: Event):
    print("world")


async def main():
    evently.publish("hello")
    await asyncio.sleep(0)


loop.run_until_complete(main())
```
<br></br>
Pass data along with an event and access it with `event.event_data`
```
@evently.subscribe("hello")
def say_world(event):
    print(event.event_type)
    print(event.event_data)
    print("world")

evently.publish("hello", {"example": "data"})
```
<br></br>
Subscribe to the same event many times
```
@evently.subscribe("hello")
def say_world(event):
    print("world")

@evently.subscribe("hello")
def say_goodbye(event):
    print("goodbye")
```
<br></br>
Subscribe to multiple events
```
@evently.subscribe(["hello", "hola"])
def say_world(event):
    if event.event_type == "hello":
        print("world")
    elif event.event_type == "hola":
        print("mundo")
```
<br></br>
Unsubscribe when you no longer want a handler to be called
```
@evently.subscribe("hello")
def say_world(event):
    print("world")

say_world.unsubscribe()
```
<br></br>
Run blocking code in an executor with the kwarg `blocking=True`
```
from time import sleep

@evently.subscribe("hello", blocking=True)
def say_world_blocking(event):
    sleep(10)
    print("world")
```
<br></br>
Receive the EventHandler instance as a kwarg by using `context=True`
```
from time import sleep

@evently.subscribe("hello", context=True)
def say_world_blocking(event, context):
    sleep(10)
    print("world")
    context.unsubscribe()
```
