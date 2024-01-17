from langchain.agents.agent_toolkits import create_conversational_retrieval_agent
from langchain.chat_models import ChatOpenAI
from langchain.tools import Tool
import os
import dotenv

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def custom_tool(state, input):
    """
    A custom tool that modifies and uses the state.
    :param state: The current state of the conversation.
    :param input: The current input from the user.
    :return: The modified state and a response.
    """

    # Accessing state variables
    user_preferences = state.get("user_preferences", {})
    conversation_history = state.get("conversation_history", [])

    # Modifying state based on the input
    if "like science" in input:
        user_preferences["topic"] = "science"
    state["user_preferences"] = user_preferences

    # Adding the input to the conversation history
    conversation_history.append(input)
    state["conversation_history"] = conversation_history

    # Generate a response (can be more complex depending on the tool's function)
    response = f"I see you're interested in {user_preferences.get('topic', 'various topics')}."

    return state, response


tools = [
    Tool(
        name="initial_retriever",
        func=custom_tool,
        description="useful for when you need initial information.")
]

# Define initial state
initial_state = {
    "user_preferences": {},
    "conversation_history": []
}

# Create the agent with the initial state
agent = create_conversational_retrieval_agent(llm=ChatOpenAI(temperature=0), tools=tools, initial_state=initial_state)

# Example of a conversation loop
while True:
    user_input = "hello"  # Function to capture user input
    agent_state = agent.get_state()  # Access the current state

    # Update state with new user input
    agent_state["conversation_history"].append(user_input)

    # Process input with the agent (which can use its tools)
    response, updated_state = agent.process_input(user_input, state=agent_state)

    # Update agent state
    agent.set_state(updated_state)

    # Tools within the agent can access and modify this state as needed

# Define initial state
initial_state = {
    "user_preferences": {},
    "conversation_history": []
}

# Create the agent with the initial state
agent = create_conversational_retrieval_agent(initial_state=initial_state)

# Example of a conversation loop
while True:
    user_input = get_user_input()  # Function to capture user input
    agent_state = agent.get_state()  # Access the current state

    # Update state with new user input
    agent_state["conversation_history"].append(user_input)

    # Process input with the agent (which can use its tools)
    response, updated_state = agent.process_input(user_input, state=agent_state)

    # Update agent state
    agent.set_state(updated_state)

    # Tools within the agent can access and modify this state as needed

# Example usage within a conversational loop
state = {
    "user_preferences": {},
    "conversation_history": []
}

user_input = "I like science"
state, response = custom_tool(state, user_input)

print("Tool Response:", response)
