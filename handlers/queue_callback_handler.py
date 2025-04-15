import asyncio
from langchain_core.callbacks import AsyncCallbackHandler

class QueueCallbackHandler(AsyncCallbackHandler):
    """ Callback handler that puts llm generated tokens into a queue"""

    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.final_answer_seen = False

    async def __aiter__(self):
        while True:
            if self.queue.empty():
                await asyncio.sleep(0.1)
                continue
            token = self.queue.get()

            if token == "<<DONE>>":
                return
            if token:
                yield token

    def on_llm_new_token(self, *args, **kwargs):
        """ Put new token into the queue. """
        chunk = kwargs.get("chunk")
        if chunk and getattr(chunk, "tool_calls", None):
            tool = chunk.tool_calls[0]
            if tool.get("name") == "final_answer":
                self.final_answer_seen = True
        self.queue.put_nowait(chunk)

    def on_llm_end(self, *args, **kwargs):
        # add <<DONE>> token to the queue if final answer seen
        if self.final_answer_seen:
            self.queue.put_nowait("<<DONE>>")
        else:
            self.queue.put_nowait("<<STEP END>>")