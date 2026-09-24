"""All V1 connectors. Instantiate fresh each run so they pick up a freshly saved .env."""

from app.connectors.claude_code import ClaudeCodeConnector
from app.connectors.github import GitHubConnector
from app.connectors.leetcode import LeetCodeConnector
from app.connectors.todoist import TodoistConnector

ALL_CONNECTORS = [GitHubConnector, LeetCodeConnector, TodoistConnector, ClaudeCodeConnector]
