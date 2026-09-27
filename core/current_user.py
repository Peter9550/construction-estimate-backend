CURRENT_USER_ID = 1


class CurrentUser:
    def __init__(self, user_id):
        self.id = user_id


current_user = None


def get_current_user():
    global current_user
    if current_user is None:
        current_user = CurrentUser(CURRENT_USER_ID)
    return current_user
