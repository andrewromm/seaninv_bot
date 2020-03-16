import asyncio

class ChatDispatcher:
    class Timeout(RuntimeError):
        def __init__(self, last_message):
            self.last_message = last_message
            super().__init__('timeout exceeded')

    def __init__(self, *,
                 chatcb,
                 shardcb = lambda message: message.from_user.id,
                 inactive_timeout = 15 * 60):
        self.chatcb = chatcb
        self.shardcb = shardcb
        self.inactive_timeout = inactive_timeout
        self.chats = {}
        self.state = {}

    async def handle(self, message, state):
        self.state = state
        shard = self.shardcb(message)

        loop = asyncio.get_event_loop()

        if shard not in self.chats:
            self.chats[shard] = {
                'task': self.create_chat(loop, shard),
                'messages': [],
                'wait': asyncio.Event(),
                'last_message': None,
            }
        self.chats[shard]['messages'].append(message)
        self.chats[shard]['wait'].set()

    def create_chat(self, loop, shard):
        async def _chat_wrapper():
            try:
                await self.chatcb(self.get_message(shard), self.cancel_state)
            finally:
                del self.chats[shard]

        return loop.create_task(_chat_wrapper())

    def get_message(self, shard):
        async def _get_message(inactive_timeout=self.inactive_timeout):
            while True:                
                if self.chats[shard]['messages']:
                    last_message = self.chats[shard]['messages'].pop(0)
                    self.chats[shard]['last_message'] = last_message
                    return last_message

                try:
                    await asyncio.wait_for(self.chats[shard]['wait'].wait(),
                                           timeout=inactive_timeout)
                except asyncio.TimeoutError:
                    self.chats[shard]['wait'].set()
                    raise self.Timeout(self.chats[shard]['last_message'])

                if not self.chats[shard]['messages']:
                    self.chats[shard]['wait'].clear()
        return _get_message

    async def cancel_state(self):
      if self.state is None:
        return
      
      await self.state.finish()