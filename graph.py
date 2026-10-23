from agent import Agent

# LangGraph CLI expects a compiled graph; API manages optional session IDs itself.
graph = Agent().create_agent().graph
