import argparse
import os
import sys
import json

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


class ExecuteTool:
    def __init__(self, tool_call):
        self.tool_call = tool_call
        self.func = tool_call.function.name
        self.args = json.loads(tool_call.function.arguments)
    def read(self):
        with open(self.args["file_path"], "r") as f:
            print(f.read())

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    messages = [{"role": "user", "content": args.p}]
    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=messages,
        tools=[
        {
            "type": "function",
            "function": {
                "name": "Read",
                "description": "Read and return the contents of a file",
                "parameters": {
                    "type": "object",
            "properties": {
                "file_path": {
                "type": "string",
                "description": "The path to the file to read"
                }
            },
            "required": ["file_path"]
            }
        }
        }
    ]
    )
    while True:
        response = chat.choices[0].message
        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        print("Logs from your program will appear here!", file=sys.stderr)
        if not response.tool_calls:
            print(response.content)
            break

        tool_calls = response.tool_calls
        for tool_call in tool_calls:
            result = ExecuteTool(tool_call)
            if result.func == "Read":
                result.read()
                messages.append({"role": "assistant", "content": response.content})
            else:
                raise RuntimeError("unknown function")
        else:
            print(chat.choices[0].message.content)

if __name__ == "__main__":
    main()
