import os

def get_aws_credentials(profile='default'):
    credentials_path = os.path.expanduser('~/.aws/credentials')
    credentials = {}

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

    with open(credentials_path, 'r') as file:
        current_profile = None
        for line in file:
            line = line.strip()  # Strip newline and surrounding whitespace

            # Skip empty lines and comments
            if not line or line.startswith('#') or line.startswith(';'):
                continue

            # Check for profile section headers
            if line.startswith('[') and line.endswith(']'):
                current_profile = line[1:-1].strip()
                continue

            # Only process lines if in the correct profile
            if current_profile == profile:
                # Split only on the first '=' to handle values with '='
                key_value = line.split('=', 1)
                if len(key_value) == 2:
                    key, value = key_value[0].strip(), key_value[1].strip()
                    credentials[key] = value

    if not credentials:
        raise ValueError(f"No credentials found for profile: {profile}")

    return credentials

def main():
    try:
        # You can change 'default' to any profile name you need
        profile = 'default'
        credentials = get_aws_credentials(profile)
        print(f"AWS credentials for profile '{profile}':")
        for key, value in credentials.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
