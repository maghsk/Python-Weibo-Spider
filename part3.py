from enum import Enum


class ClientMessage(Enum):
    STRING = 0
    SUBSCRIBE = 1
    UNSUBSCRIBE = 2
    UPDATE_TOPIC = 3
    ALIVE = 4
    DIED = 5
    GET_BLOG = 6
    KEYWORD_QUERY = 7


class ServerMessage(Enum):
    STRING = 0
    ASK_ALIVE = 1
    NEW_BLOG = 2
    KICK = 3
    WELCOME = 4
    DONE = 5
    UNAVAILABLE = 6

