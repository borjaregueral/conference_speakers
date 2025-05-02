import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def find_env_files(directory):
    """Find all .env files in the given directory and its subdirectories."""
    env_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.env') or file == '.env':
                env_path = os.path.join(root, file)
                env_files.append(env_path)
    return env_files

def check_env_file(env_file):
    """Check if the .env file contains an OpenAI API key."""
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            if 'OPENAI_API_KEY' in content:
                # Extract the API key
                for line in content.splitlines():
                    if line.strip().startswith('OPENAI_API_KEY'):
                        key = line.split('=')[1].strip().strip('"').strip("'")
                        if key:
                            masked_key = f"{key[:4]}...{key[-4:]}"
                            logger.info(f"Found OPENAI_API_KEY in {env_file}: {masked_key}")
                        else:
                            logger.info(f"Found OPENAI_API_KEY in {env_file}, but it's empty")
                        return True
            else:
                logger.info(f"No OPENAI_API_KEY found in {env_file}")
                return False
    except Exception as e:
        logger.error(f"Error reading {env_file}: {e}")
        return False

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Find all .env files
logger.info(f"Searching for .env files in {current_dir}...")
env_files = find_env_files(current_dir)

if env_files:
    logger.info(f"Found {len(env_files)} .env files:")
    for env_file in env_files:
        logger.info(f"Checking {env_file}...")
        check_env_file(env_file)
else:
    logger.info("No .env files found")

# Also check for any Python files that might be setting the API key
logger.info(f"Searching for Python files that might be setting the API key...")
for root, dirs, files in os.walk(current_dir):
    for file in files:
        if file.endswith('.py'):
            py_path = os.path.join(root, file)
            try:
                with open(py_path, 'r') as f:
                    content = f.read()
                    if 'openai.api_key' in content and 'OPENAI_API_KEY' in content:
                        logger.info(f"Found potential API key setting in {py_path}")
                        # Extract the relevant lines
                        for i, line in enumerate(content.splitlines()):
                            if 'openai.api_key' in line or 'OPENAI_API_KEY' in line:
                                logger.info(f"  Line {i+1}: {line.strip()}")
            except Exception as e:
                logger.error(f"Error reading {py_path}: {e}")