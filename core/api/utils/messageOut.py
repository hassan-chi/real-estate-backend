from ninja import Schema


class MessageOut(Schema):
    title: str
    message: str