from tortoise.models import Model
from tortoise import fields


class PanasonicProjector(Model):
    id = fields.IntField(pk=True)
    ip = fields.CharField(max_length=50, default="")
    name = fields.CharField(max_length=50, default="")
    last_message = fields.CharField(max_length=200, default="No messages received")
