from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableSerializable
import json
from setup import llm, prompt
from tools.tool import tools, tool_func_map
from handlers.queue_callback_handler import QueueCallbackHandler

class CustomAgentExecutor:
    def __init__(self, max_iterations: int = 5):
        self.chat_history: list[BaseMessage] = []
        self.max_iterations = max_iterations
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

    async def invoke(self, database_schema: str, input: str, streamer: QueueCallbackHandler):
        count = 0
        agent_scratchpad = []
        
        # stream the llm response
        async def stream(query: str) -> list[AIMessage]:
            response = self.agent.with_config(
                callbacks=[streamer]
            )

            # to store the streamed AIMessageChunk objects
            output = None

            async for token in response.astream({
                "database_schema":database_schema,
                "input": query,
                "chat_history": self.chat_history,
                "agent_scratchpad": []
            }):
                tool_calls = getattr(token, "tool_calls", None)
                if tool_calls:
                    if output:
                        output += token
                    else:
                        output = token
                else:
                    pass
            # return a single AI message since no more than one tool will be called at once
            return AIMessage(
                content=output.content,
                tool_calls=output.tool_calls
            )
        found_final_answer = False
        while count < self.max_iterations:
            tool_call = await stream(query=input)

            tool_name = tool_call.tool_calls[0]["name"]
            tool_args = tool_call.tool_calls[0]["args"]

            tool_execution_content = tool_func_map[tool_name](**tool_args)

            tool_exec = ToolMessage(
                content=f"The {tool_name} tool returned {tool_execution_content}",
                tool_call_id = tool_call.tool_calls[0]["id"]
            )

            # extend the agent scratchpad
            agent_scratchpad.extend([tool_call, tool_exec])
            count += 1

            if tool_name == "final_answer":
                found_final_answer = True
                break

        final_answer = tool_args if found_final_answer else {"answer":"No answer found", "tools_used":[]}
        self.chat_history.extend([
            HumanMessage(content=input),
            AIMessage(content=json.dumps(final_answer))
        ])
        return final_answer