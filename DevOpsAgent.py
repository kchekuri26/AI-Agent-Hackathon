import os
import json
import anthropic
from dotenv import load_dotenv
import subprocess
import re
import time

load_dotenv()

SYS_PROMPT = """
You are a DevOps expert. You will be prompted by the users to generate AWS CLI commands to process complex requests. Generate only AWS CLI commands and nothing else (no other texts). Chain commands with '&&'. Your output will only be executable AWS CLI commands
because we are running that in the shell directly!!!

Account ID: {accountId}
IAM user: {iamUser}
Region: {region}
"""
class DevOpsAgent:
    def __init__(self, account_id, iam_user, region):
        self.model = "claude-3-5-sonnet-20240620"
        self.client = anthropic.Anthropic()
        self.results = {
            "commands": [],
            "results": []
        }
        self.accountId = account_id
        self.iamUser = iam_user
        self.region = region

    def generate_aws_cli_commands(self, user_prompt, system_prompt):
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return message.content[0].text.strip()

    def execute_aws_cli_command(self, command):
        try:
            if "create-table" in command:
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                print("Waiting for table to become active...")
                time.sleep(15) 
                return result.stdout.strip()
            else:
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error executing AWS CLI command: {e.stderr.strip()}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def generate_aws_cli_processed(self, user_prompt, system_prompt):
        generated_output = self.generate_aws_cli_commands(user_prompt, system_prompt.format(
            result=self.results,
            accountId=self.accountId,
            iamUser=self.iamUser,
            region=self.region
        ))
        commands = generated_output.split("&&")
        return commands

    def process_user_request(self, user_prompt):
        commands = self.generate_aws_cli_processed(user_prompt, SYS_PROMPT)
        for command in commands:
            print(f"Executing: {command}\n")
            result = self.execute_aws_cli_command(command)
            self.results["commands"].append(command)
            print(f"Result: {result}\n")
            self.results["results"].append(result)

            if "Error" in result:
                print("An error occurred. Stopping execution.")
                break
        return self.results

if __name__ == "__main__":
    account_id = input("Enter your AWS Account ID: ")
    iam_user = input("Enter your IAM user name: ")
    region = input("Enter your AWS region: ")

    agent = DevOpsAgent(account_id, iam_user, region)
    
    user_request = input("Enter your DevOps request: ")
    result = agent.process_user_request(user_request)
    
    print("\nExecution Summary:")
    for cmd, res in zip(result["commands"], result["results"]):
        print(f"Command: {cmd}")
        print(f"Result: {res}\n")