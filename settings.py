import uio
import ujson

def settings(file_path, data=None):
    try:
        if data is None:
            # Read existing JSON data from the file
            try:
                with uio.open(file_path, 'r') as f:
                    json_data = f.read()
                    return ujson.loads(json_data)
            except (OSError, ValueError):
                return {}  # Return an empty dictionary if reading fails
        
        # Read existing JSON data from the file, if it exists
        try:
            with uio.open(file_path, 'r') as f:
                existing_data = ujson.loads(f.read())
        except (OSError, ValueError):
            existing_data = {}

        # Update existing data with new data
        existing_data.update(data)

        # Convert the combined data back to JSON format
        modified_json_data = ujson.dumps(existing_data)

        # Write the modified JSON data back to the file
        with uio.open(file_path, 'w') as f:
            f.write(modified_json_data.encode('utf-8'))

        return True 

    except Exception as e:
        print("Error:", e)
        return False  

# Usage
# # Read data from the file
# setting = settings("settings.json")
# print(setting)

# # Modify and write data to the file
# new_data = {
#     'option': 'new_value1',
#     'option3': 'value3'
# }
# write_result = settings("settings.json", new_data)
# print("Write result:", write_result)

