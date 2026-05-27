import os

# Keep unit tests isolated from developer .env (CORAL_MODE=cli, real tokens, etc.)
os.environ["CORAL_MODE"] = "mock"
