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
            return f.read()

    def write(self):
        with open(self.args["file_path"], "w") as f:
            f.write(self.args["content"])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [{"role": "user", "content": args.p}]
    while True:
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
        response = chat.choices[0].message
        message_dict = {"role": "assistant", "content": response.content}
        if hasattr(response, "tool_calls") and response.tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in response.tool_calls
            ]
        messages.append(message_dict)
        if not message_dict.get("tool_calls"):
            print(response.content)
            break
        for tc in response.tool_calls:
            result = ExecuteTool(tc)
            if result.func == "Read":
                file_content = result.read()
            elif result.func == "Write":
                result.write()
                file_content = "File written successfully"
            else:
                file_content = "Unknown function"
            messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": file_content,
                    }
                )



if __name__ == "__main__":
    main()
