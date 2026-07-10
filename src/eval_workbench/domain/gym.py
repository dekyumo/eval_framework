from pydantic import BaseModel


class Gym(BaseModel):
    """A POMDP environment for agentic-user simulations.

    Points to a fully-qualified class in the target repo. The class is
    constructed from a config dict (`GymClass(config)`); its bound methods
    are exposed as tools to the user and/or solver agents, and one bound
    method serves as the termination predicate.
    """

    id: str
    name: str
    class_path: str          # "package.module.ClassName" (split on the last dot)
    description: str = ""
