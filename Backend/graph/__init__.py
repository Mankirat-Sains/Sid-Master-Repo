"""LangGraph package."""

# Avoid importing build_graph here to prevent circular imports when submodules
# (e.g., router_dispatcher -> graph.subgraphs...) trigger package import.
# Import build_graph directly from graph.builder where needed.
