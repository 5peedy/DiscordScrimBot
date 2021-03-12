from utils import Notification


def role_mentioned(ctx):
    if len(ctx.message.role_mentions) != 0:
        return True
    else:
        message = "No role mentioned"
        print(message)
        Notification.send_notification(ctx=ctx, header=message)
        return False

