from plugins.user.utils.chats_locks import ChatsLocks

blocking_new_messages = ChatsLocks('new')
blocking_editable_messages = ChatsLocks('edit')


blocking_messages = ChatsLocks('all')
