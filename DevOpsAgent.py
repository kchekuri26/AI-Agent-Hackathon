import anthropic
from dotenv import load_dotenv
import subprocess
import time
from rich.prompt import Prompt
from rich import print
from rich.console import Console

console = Console()

load_dotenv()

SYS_PROMPT = """
You are a DevOps expert. You will be prompted by the users to generate AWS CLI commands to process complex requests. Generate only AWS CLI commands and nothing else (no other texts). Chain commands with '&&'. Your output will only be executable AWS CLI commands
because we are running that in the shell directly!!!

Account ID: {accountId}
IAM user: {iamUser}
Region: {region}
"""

RETRY_PROMPT = """
You are a DevOps expert. You are prompted to generate AWS CLI commands based on user request but you generated the wrong command. Based
on the error message, correct your command. Only output an AWS CLI command and nothing else (no other texts). Your output will only be executable AWS CLI commands
because we are running that in the shell directly!!!

Original command: {originalCommand}
Error message: {error}

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

    def error_retry(self, retry_prompt):
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0,
            system=retry_prompt,
            messages=[{"role": "user", "content": retry_prompt}]
        )
        return message.content[0].text.strip()


    def execute_aws_cli_command(self, command):
        with console.status("[bold yellow]Provisioning resources...") as status:
            try:
                if "create-table" in command:
                    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                    time.sleep(15) 
                else:
                    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as error:
                # Retry three times
                for _ in range(3):
                    try:
                        command = self.error_retry(RETRY_PROMPT.format(
                            originalCommand = command,
                            error=error.stderr.strip()
                        ))
                        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                        return result.stdout.strip()
                    except subprocess.CalledProcessError as e:
                        error = e
                        continue
                # If all retries fail
                console.clear()
                print("[bold red]❌ Failed to create resources after 3 attempts[/bold red]")
                return f"Error executing AWS CLI command: {error.stderr.strip()}"
            except Exception as e:
                console.clear()
                print("[bold red]❌ An unexpected error occurred[/bold red]")
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
        count = 0
        for command in commands:
            self.execute_aws_cli_command(command)
            count += 1
            console.clear()
            console.log(f"Resources created: {count}")

            # self.results["commands"].append(command)
            # self.results["results"].append(result)

            # if "Error" in result:
                # print("An error occurred. Stopping execution.")
                # break
        return self.results

if __name__ == "__main__":
    account_id = Prompt.ask("[bold]Enter your AWS Account ID[/bold]")
    iam_user = Prompt.ask("[bold]Enter your IAM user name[/bold]")
    region = Prompt.ask("[bold]Enter your AWS region[/bold]", choices=["us-west-2", "us-east-1", "us-east2"], default="us-west-2")

    print("[bold green]Successfully linked your AWS account!\n[/bold green]")

    agent = DevOpsAgent(account_id, iam_user, region)
    
    user_request = Prompt.ask("[bold]Enter your request[/bold]")
    agent.process_user_request(user_request)
    console.clear()
    print("[bold green]🎉 Resources created![bold green]")

    # print("\nExecution Summary:")
    # for cmd, res in zip(result["commands"], result["results"]):
    #     print(f"Command: {cmd}")
    #     print(f"Result: {res}\n")