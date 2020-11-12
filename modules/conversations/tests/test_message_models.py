from conversations.models import Conversation, Message


def test_conversation_save(conversation):
    """ also tests message.save() since we must create a message to save """
    message = Message(
        user_id=conversation.user_id,
        conversation_id=conversation.id,
        message="Hello World",
    )
    conversation.save(message=message)
    assert conversation.shared_id is not None


def test_first_message(conversation_msgs, user):
    conversation = conversation_msgs
    assert conversation.first_message.message == "First message"


def test_last_message(conversation_msgs, user):
    conversation = conversation_msgs
    assert conversation.last_message.message == "Second message"

    message = Message(user_id=user.id, message="Third message")
    conversation.save(message=message)
    assert conversation.last_message.message != "Second message"


def test_delete_user_with_conversations(conversation_msgs, user):
    assert user.delete()
