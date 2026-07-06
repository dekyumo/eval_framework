import os

# Malformed because it throws an exception on import
raise RuntimeError("Boom!")

from google.adk.agents import Agent

root_agent = Agent(
    name="root_agent",
    instructions="You are a helpful assistant.",
    tools=[]
)
