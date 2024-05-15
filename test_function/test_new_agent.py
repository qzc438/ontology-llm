import run_config as config
from langchain_core.tools import tool
from operator import itemgetter
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent


@tool
def multiply(first_int: int, second_int: int) -> int:
    """Multiply two integers together."""
    return first_int * second_int


print(multiply.name)
print(multiply.description)
print(multiply.args)

print(multiply.invoke({"first_int": 4, "second_int": 5}))

llm = config.llm
llm_with_tools = llm.bind_tools([multiply])
msg = llm_with_tools.invoke("whats 5 times forty two")
print(msg)
print(msg.tool_calls)

chain = llm_with_tools | (lambda x: x.tool_calls[0]["args"]) | multiply
print(chain.invoke("What's four times 23"))

# Get the prompt to use - can be replaced with any prompt that includes variables "agent_scratchpad" and "input"!
prompt = hub.pull("hwchase17/openai-tools-agent")
print(prompt.pretty_print())

@tool
def add(first_int: int, second_int: int) -> int:
    "Add two integers."
    return first_int + second_int

@tool
def exponentiate(base: int, exponent: int) -> int:
    "Exponentiate the base to the exponent power."
    return base**exponent


tools = [multiply, add, exponentiate]
# Construct the tool calling agent
agent = create_tool_calling_agent(llm, tools, prompt)
# Create an agent executor by passing in the agent and tools
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
agent_executor.invoke(
    {
        "input": "Take 3 to the fifth power and multiply that by the sum of twelve and three, then square the whole result"
    }
)