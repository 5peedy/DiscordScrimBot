from utils import Notification


def role_mentioned(ctx):
    if len(ctx.message.role_mentions) != 0:
        return True
    else:
        message = "No role mentioned"
        print(message)
        Notification.send_alert(ctx=ctx, header=message, content="")
        return False


def is_numeric(message):
    return message.content.isnumeric()


class Checks:
    def __init__(self, client):
        self.db = client.db

    def is_admin(self, ctx):
        return self.db.is_admin(ctx=ctx, server_id=ctx.guild.id, member=ctx.message.author)
