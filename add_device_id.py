import sys
import sqlite3

DATABASE = 'terradetect.db'

def add_device_id(device_id):
    conn = sqlite3.connect(DATABASE)
    try:
        conn.execute('INSERT INTO device_ids (device_id, registered) VALUES (?, 0)', (device_id,))
        conn.commit()
        print(f"Device ID {device_id} added successfully.")
    except sqlite3.IntegrityError:
        print(f"Device ID {device_id} already exists.")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_device_id.py <DEVICE_ID>")
        sys.exit(1)
    device_id = sys.argv[1]
    if len(device_id) != 6:
        print("Device ID must be exactly 6 characters.")
        sys.exit(1)
    add_device_id(device_id)