class ScannerError(Exception):
    pass

# Caller Errors
class CallerError(ScannerError):
    pass

class RepoNotFoundError(CallerError):
    pass

class CommitNotFoundError(CallerError):
    pass

class DirtyRepositoryError(CallerError):
    pass

# Agent Errors
class AgentError(ScannerError):
    pass

class AgentEntrypointNotFound(AgentError):
    pass

class UnsupportedAgentStructure(AgentError):
    pass

class AgentImportError(AgentError):
    pass

# Framework Errors
class FrameworkError(ScannerError):
    pass

class ScannerInternalError(FrameworkError):
    pass
