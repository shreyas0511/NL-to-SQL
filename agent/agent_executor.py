from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableSerializable
import json
from setup import llm, prompt
from tools.tool import tools, tool_func_map

class CustomAgentExecutor:
    def __init__(self):
        self.chat_history: list[BaseMessage] = []
        self.max_iterations: int = 5
        self.agent: RunnableSerializable = (
            {
                "database_schema": lambda x: x["database_schema"],
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: x["agent_scratchpad"]
            }
            | prompt
            | llm.bind_tools(tools, tool_choice="any")
        )

    def invoke(self, database_schema: str, input: str):
        # keep invoking the agent iteratively in a loop until we get the final answer
        count = 0

        # this is temporary storage for each agent execution loop, so we only define it here
        agent_scratchpad = []

        while count < self.max_iterations:
            # invoke one iteration of the agent
            tool_call = self.agent.invoke(
                {
                    "database_schema": database_schema,
                    "input": input,
                    "chat_history": self.chat_history,
                    "agent_scratchpad": agent_scratchpad
                }
            )

            # add initial tool call to the scratchpad
            agent_scratchpad.append(tool_call)

            # get the tool name and arguments
            tool_name = tool_call.tool_calls[0]["name"]
            tool_args = tool_call.tool_calls[0]["args"]

            # now execute the tool and add output to the scratchpad
            tool_execution_content = tool_func_map[tool_name](**tool_args)

            tool_exec = ToolMessage(
                content=f"The {tool_name} tool returned {tool_execution_content}",
                tool_call_id = tool_call.tool_calls[0]["id"]
            )
            agent_scratchpad.append(tool_exec)

            # check if the current tool is the final answer tool
            if tool_name == "final_answer":
                break
        
        # add the human input and AI final answer to chat history
        final_answer = tool_execution_content
        self.chat_history.extend([
            HumanMessage(content=input),
            AIMessage(content=str(final_answer))
        ])

        # return final answer in json format
        return json.dumps(final_answer)
            