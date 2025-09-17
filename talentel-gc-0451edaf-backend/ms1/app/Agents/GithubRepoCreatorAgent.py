from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.agents import UserProxyAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
import requests
import json
import os
from typing import Dict, Any

# Model client setup
model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4.1",
    model="gpt-4.1",
    api_version="2024-06-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

class GitHubRepoCreator:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def create_repository(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/user/repos"
        
        try:
            print("[DEBUG] Payload sent to GitHub API:", json.dumps(repo_data, indent=2))
            response = requests.post(url, headers=self.headers, json=repo_data)
            print("[DEBUG] GitHub API response status:", response.status_code)
            print("[DEBUG] GitHub API response content:", response.text)
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json(),
                "message": f"Repository '{repo_data['name']}' created successfully!"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create repository: {str(e)}",
                "response": response.text if 'response' in locals() else None
            }

def get_user_input_and_approval():
    """Get all user input and approval in one step."""
    
    print("\n" + "="*50)
    print("🚀 GitHub Repository Creation Assistant")
    print("="*50)
    
    while True:
        # Get repository details
        repo_name = input("Repository name: ").strip()
        if not repo_name:
            print("❌ Repository name cannot be empty. Please try again.")
            continue
            
        repo_description = input("Repository description (optional): ").strip()
        
        # Ask about optional features
        init_readme = input("Initialize with README? (y/n, default y): ").strip().lower()
        init_readme = init_readme != 'n'
        
        gitignore = input("Gitignore template (e.g., Python, Node, optional): ").strip()
        license_template = input("License template (e.g., mit, apache-2.0, optional): ").strip()
        
        # Show review
        print(f"\n📋 Review the repository parameters:")
        print(f"Name: {repo_name}")
        print(f"Description: {repo_description or 'None'}")
        print(f"Initialize with README: {init_readme}")
        print(f"Gitignore template: {gitignore or 'None'}")
        print(f"License template: {license_template or 'None'}")
        print(f"Privacy: Private (enforced)")
        
        # Get final approval
        while True:
            approval = input("\nDo you approve these parameters? (y/n): ").strip().lower()
            if approval == 'y':
                return {
                    "name": repo_name,
                    "description": repo_description,
                    "auto_init": init_readme,
                    "gitignore_template": gitignore,
                    "license_template": license_template,
                    "approved": True
                }
            elif approval == 'n':
                print("Let's try again with different parameters...\n")
                break  # Go back to input collection
            else:
                print("Please enter 'y' for yes or 'n' for no.")

def create_repository_directly(github_creator: GitHubRepoCreator, repo_params: Dict[str, Any]) -> str:
    """Create repository directly without agent interaction."""
    
    # Prepare repository data
    repo_data = {
        "name": repo_params["name"],
        "description": repo_params["description"],
        "private": True,  # Always enforce private
        "auto_init": repo_params["auto_init"],
    }
    
    # Add optional parameters
    if repo_params["gitignore_template"]:
        repo_data["gitignore_template"] = repo_params["gitignore_template"]
    if repo_params["license_template"]:
        repo_data["license_template"] = repo_params["license_template"]
    
    print(f"\n🚀 Creating repository '{repo_params['name']}'...")
    
    # Create the repository
    result = github_creator.create_repository(repo_data)
    
    if result["success"]:
        repo_info = result["data"]
        success_msg = f"""✅ Repository created successfully!

🔗 Repository URL: {repo_info['html_url']}
📁 Clone URL: {repo_info['clone_url']}
🔒 Privacy: Private
📝 Description: {repo_info.get('description', 'No description')}"""
        print(success_msg)
        return repo_info['html_url']
    else:
        error_msg = f"❌ Error creating repository: {result['message']}"
        print(error_msg)
        raise Exception(result['message'])

def setup_simple_agents(github_creator: GitHubRepoCreator, repo_params: Dict[str, Any]):
    """Set up simple agents that just confirm the repository creation."""
    
    # No input function needed - we already have approval
    user_proxy = UserProxyAgent(
        name="user_proxy",
        input_func=lambda prompt: "Repository creation confirmed. Proceed.",
    )
    
    github_assistant = AssistantAgent(
        name="github_assistant",
        model_client=model_client,
        system_message=f"""You are a GitHub repository creation assistant.

The user has already approved the creation of a repository with these parameters:
- Name: {repo_params['name']}
- Description: {repo_params['description']}
- Public: yes 
- Initialize with README: {repo_params['auto_init']}
- Gitignore: {repo_params['gitignore_template'] or 'None'}
- License: {repo_params['license_template'] or 'None'}

Your job is to:
1. Acknowledge the repository creation request
2. Confirm that you will create the repository with the approved parameters
3. Call the repository creation function
4. Report the result and end with "TERMINATE"

Do not ask for any additional input or confirmation. The user has already approved everything.
"""
    )
    
    return user_proxy, github_assistant

class SimpleGitHubAgent(AssistantAgent):
    """Simplified GitHub agent that creates repositories without additional prompts."""
    
    def __init__(self, github_creator: GitHubRepoCreator, repo_params: Dict[str, Any]):
        super().__init__(
            name="github_assistant",
            model_client=model_client,
            system_message="You are a GitHub repository creation assistant. Create the repository as requested and report the result."
        )
        self.github_creator = github_creator
        self.repo_params = repo_params
    
    async def on_messages(self, messages, cancellation_token=None):
        """Handle messages and create repository."""
        
        try:
            # Create repository directly
            repo_url = create_repository_directly(self.github_creator, self.repo_params)
            
            response_message = f"""Repository created successfully!

Repository URL: {repo_url}

The repository has been created with your approved parameters and is ready to use.

TERMINATE"""
            
            from autogen_agentchat.messages import TextMessage
            return TextMessage(content=response_message, source=self.name)
            
        except Exception as e:
            error_message = f"Error creating repository: {str(e)}\n\nTERMINATE"
            from autogen_agentchat.messages import TextMessage
            return TextMessage(content=error_message, source=self.name)

def main():
    """Main function with simplified flow."""
    
    # Check for required environment variables
    required_vars = ["GITHUB_TOKEN", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    try:
        # Initialize GitHub creator
        print("🔧 Initializing GitHub repository creator...")
        github_creator = GitHubRepoCreator(GITHUB_TOKEN)
        
        # Get user input and approval (all in one step)
        repo_params = get_user_input_and_approval()
        
        if not repo_params["approved"]:
            print("❌ Repository creation cancelled.")
            return
        
        # Option 1: Direct creation (recommended for your use case)
        print("\n🤖 Creating repository directly...")
        try:
            repo_url = create_repository_directly(github_creator, repo_params)
            print(f"\n🎉 Success! Repository created at: {repo_url}")
            return repo_url
        except Exception as e:
            print(f"❌ Failed to create repository: {str(e)}")
            return None
        
        # Option 2: Using agents (if you specifically need AutoGen)
        # Uncomment the code below if you want to use agents
        """
        print("\n🤖 Setting up AutoGen agents...")
        
        # Create simple agent
        github_agent = SimpleGitHubAgent(github_creator, repo_params)
        user_proxy = UserProxyAgent(
            name="user_proxy",
            input_func=lambda prompt: "Proceed with repository creation."
        )
        
        # Set up termination
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([user_proxy, github_agent], termination_condition=termination)
        
        # Run the task
        import asyncio
        result = asyncio.run(team.run_stream(task="Create the approved repository."))
        
        # Process results
        async for message in result:
            if hasattr(message, 'content'):
                print(f"\n{message.source}: {message.content}")
        """
        
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

# For API/web service usage
def create_repo_api(repo_name: str, description: str = "", gitignore: str = "", license_template: str = "") -> Dict[str, Any]:
    """API function for creating repositories without interactive prompts."""
    
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        return {"success": False, "error": "GitHub token not configured"}
    
    try:
        github_creator = GitHubRepoCreator(GITHUB_TOKEN)
        
        repo_params = {
            "name": repo_name,
            "description": description,
            "auto_init": True,
            "gitignore_template": gitignore,
            "license_template": license_template,
            "approved": True
        }
        
        repo_url = create_repository_directly(github_creator, repo_params)
        
        return {
            "success": True,
            "repository_url": repo_url,
            "message": "Repository created successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create repository: {str(e)}"
        }

if __name__ == "__main__":
    main()
