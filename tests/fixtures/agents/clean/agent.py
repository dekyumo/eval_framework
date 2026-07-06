from google.adk.agents import Agent

def my_tool(x: int) -> int:
    return x * 2

root_agent = Agent(
    name="root_agent",
    instructions="You are a helpful assistant.",
    tools=[my_tool]
)
