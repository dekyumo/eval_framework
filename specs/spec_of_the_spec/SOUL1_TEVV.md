The evaluations follow the TEVV concept.
This is one of the requirements included in the NIST standards for AI/ML governance.

TEVV means:
Test: technical tests, the software works (the agentic program is without bugs), this can be units tests
Evaluation: functional tests, the agentic program gives correct domain output give correct domain input
Verification: the agentic program works as described in the specs
Validation: the agentic program works as necessary in the domain

In current practice, Test and Evaluation are a continuum, with fast technical tests running with the linter, medium length tests with every PR and long tests with every release (Annie Wang's pyramid).

To summarise, TEVV helps ensure that testing is comprehensive, by requiring technical and domain tests, and technical and domain documentation matching the outcome.

Also, because TEVV includes testing, it also includes all the concepts of computer program testing:
- coverage
- sandboxing/mocking

=====================

Use in the evaluation framework:

- a spec is derived from the agent