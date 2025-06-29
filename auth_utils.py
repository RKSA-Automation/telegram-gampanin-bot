# auth_utils.py

def load_authorized_users():
    try:
        with open("authorized_users.txt", "r") as f:
            return set(int(line.strip()) for line in f if line.strip().isdigit())
    except FileNotFoundError:
        return set()

def save_authorized_user(user_id: int):
    with open("authorized_users.txt", "a") as f:
        f.write(f"{user_id}\n")
