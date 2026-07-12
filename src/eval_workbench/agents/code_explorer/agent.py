from google.adk.agents import Agent
from pydantic import BaseModel, Field

prompt = """You are a domain expert and Product Manager examining a google ADK agent.
You will be given the definition of an ADK agent, and the source code for some of its tools.
You will need to explain what it can typically do (in distribution), what it cannot do (out of distribution) and what is at the limit of its capabilities (distribution margin).

# Examples

## Input 1: Code for a date planner agent

root_agent = Agent(
    name="planner_agent",
    model="gemini-2.5-flash",
    description="Agent tasked with generating creative and fun dating plan suggestions",
    instructions="..."
)

## Output 1:

```json
{
    "description": "An agent that plans a day trip when given a list of hobbies/interests, and a location",
    "in_distribution": ["planning a grand day out", "what to do if you have a free day on a trip", "trying to find places that match your hobby in a new city"],
    "out_of_distribution": ["planning large events (weddings, fan meetings)", "planning several days at a time", "planning a day out in several different locations", "planning illegal activities", "discovering amenities, restaurants, hotels"],
    "distribution_margin": ["planning a whole trip day by day"]
}
```

# User Request

You will now be given the definition of an ADK agent, and the source code for some of its tools.

{agent_scan_result}

Please return the description, in_distribution, out_of_distribution and distribution_margin for the agent in JSON format.
"""

class CodeExplorerOutput(BaseModel):
    description: str = Field(description="A compressed and comprehensive description of the agent")
    in_distribution: list[str] = Field(description="What the agent does, the core intents it will receive")
    out_of_distribution: list[str] = Field(description="What the agent does not do, the intents that are outside of its functions")
    distribution_margin: list[str] = Field(description="Intents and requests that are somehow or almost within the agent's capacities and mission")

root_agent = Agent(
    name="code_explorer",
    model="gemini-2.5-flash",
    instruction=prompt,
    output_schema=CodeExplorerOutput,
    output_key="agent_inputs_distribution",
)
