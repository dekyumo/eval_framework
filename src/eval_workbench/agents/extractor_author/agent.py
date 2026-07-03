"""Extractor author agent (AGENT4).
This agent writes a function to extract a given
value from a trace.

Example extractor function:

# for math problems
def extract_last_numerical(trace):
    return re.search(r'\d+', trace[-1].text).group(0)

# check tool use
def has_search_tool_use(trace):
    return any(tool_call.name == "search" for tool_call in trace where tool_call.type="tool_call" and tool_call.name == "google_search")

The extracted value will typically be compared to a ground truth provided by the user.
"""

from google.adk.agents import LlmAgent

from textwrap import dedent

import inspect
from domain.trace import Trace, MessagePart
trace_declaration = inspect.getsource(Trace)
message_part_declaration = inspect.getsource(MessagePart)

prompt = 
f"""You are an expert in writing python code for agentic systems. 
You are asked to write a python function that will take a trace as input and return a value of interest.

# Input type definition for the new function

The type definition of trace and message part are as follows:

{message_part_declaration}

{trace_declaration}

# Examples

Example 1: get the last dollar value in the text parts of the trace

import re
pattern = r"\$[0-9,]+(?:\.[0-9]{{2}})?"

def extract(trace):
    ret_value = None
    for part in trace.parts:
        if part.text is None or "$" not in part.text: continue
        dollar_values = re.findall(pattern, part.text)
        for dv in dollar_values:
            ret_value = float(dv[1:])
            
    return ret_value

Now, the user will ask you to write a function that takes a trace as input and returns a value of interest.
Return the code for the new function, without any additional text or comments.

"""
def ExtractorReturnType(BaseModel):
    python_code: str = Field(description="The python code for the new function.")
    implementation_notes: str = Field(description="Any implementation notes the requester may want to know, in markdown format.")

root_agent = LlmAgent(
    name="extractor-author",
    description="Writes python code to extract a value from a trace.",
    instruction=prompt,
    output_type=ExtractorReturnType,
    model="gemini-2.0-flash",
)
