import uuid

def get_machine_id():
    mac = uuid.getnode()
    return f"{mac:012x}"  # Format as 12-digit hex string

if __name__ == "__main__":
    machine_id = get_machine_id()
    print("Your Machine ID:", machine_id)
