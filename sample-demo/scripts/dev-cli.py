#!/usr/bin/env python3
"""
DevOps CLI Tool for EKS Sample Application
Provides utilities for log tailing and Helm rollbacks across environments
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from typing import List, Optional, Dict, Any


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class DevOpsCLI:
    """Main CLI class for DevOps operations"""
    
    def __init__(self):
        self.app_name = "sample-app"
        self.valid_environments = ["dev", "stage", "prod"]
        self.cluster_prefix = "demo-eks"
        self.region = "us-west-2"
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Print formatted log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color_map = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED
        }
        color = color_map.get(level, Colors.WHITE)
        print(f"{color}[{timestamp}] {level}: {message}{Colors.RESET}")
    
    def run_command(self, command: List[str], capture_output: bool = False) -> Optional[str]:
        """Execute shell command and return output"""
        try:
            self.log(f"Executing: {' '.join(command)}")
            if capture_output:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                return result.stdout.strip()
            else:
                subprocess.run(command, check=True)
                return None
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}", "ERROR")
            if capture_output and e.stdout:
                self.log(f"Output: {e.stdout}", "ERROR")
            if capture_output and e.stderr:
                self.log(f"Error: {e.stderr}", "ERROR")
            return None
        except FileNotFoundError:
            self.log(f"Command not found: {command[0]}", "ERROR")
            return None
    
    def validate_environment(self, environment: str) -> bool:
        """Validate environment name"""
        if environment not in self.valid_environments:
            self.log(f"Invalid environment: {environment}. Valid options: {self.valid_environments}", "ERROR")
            return False
        return True
    
    def update_kubeconfig(self, environment: str) -> bool:
        """Update kubeconfig for the specified environment"""
        cluster_name = f"{self.cluster_prefix}-{environment}"
        command = [
            "aws", "eks", "update-kubeconfig",
            "--region", self.region,
            "--name", cluster_name
        ]
        return self.run_command(command) is not None
    
    def get_pods(self, environment: str, namespace: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get list of application pods"""
        if namespace is None:
            namespace = environment
        
        command = [
            "kubectl", "get", "pods",
            "-n", namespace,
            "-l", f"app.kubernetes.io/name={self.app_name}",
            "-o", "json"
        ]
        
        output = self.run_command(command, capture_output=True)
        if output:
            try:
                data = json.loads(output)
                return data.get("items", [])
            except json.JSONDecodeError:
                self.log("Failed to parse pod information", "ERROR")
        return None
    
    def tail_logs(self, environment: str, follow: bool = False, lines: int = 100, 
                  pod_name: Optional[str] = None, namespace: Optional[str] = None) -> None:
        """Tail application logs"""
        if not self.validate_environment(environment):
            return
        
        if namespace is None:
            namespace = environment
        
        self.log(f"Tailing logs for {self.app_name} in {environment} environment")
        
        # Update kubeconfig
        if not self.update_kubeconfig(environment):
            return
        
        # Get pods if no specific pod is provided
        if pod_name is None:
            pods = self.get_pods(environment, namespace)
            if not pods:
                self.log("No pods found", "ERROR")
                return
            
            if len(pods) == 1:
                pod_name = pods[0]["metadata"]["name"]
                self.log(f"Using pod: {pod_name}", "INFO")
            else:
                self.log("Multiple pods found:", "INFO")
                for i, pod in enumerate(pods):
                    status = pod["status"]["phase"]
                    self.log(f"  {i}: {pod['metadata']['name']} ({status})")
                
                try:
                    choice = int(input(f"{Colors.CYAN}Select pod (0-{len(pods)-1}): {Colors.RESET}"))
                    if 0 <= choice < len(pods):
                        pod_name = pods[choice]["metadata"]["name"]
                    else:
                        self.log("Invalid selection", "ERROR")
                        return
                except (ValueError, KeyboardInterrupt):
                    self.log("Operation cancelled", "WARNING")
                    return
        
        # Build kubectl logs command
        command = ["kubectl", "logs", pod_name, "-n", namespace, "--tail", str(lines)]
        if follow:
            command.append("-f")
        
        self.log(f"Starting log tail for pod {pod_name}...")
        self.log(f"Press Ctrl+C to stop", "INFO")
        
        try:
            # For following logs, don't capture output
            if follow:
                subprocess.run(command)
            else:
                output = self.run_command(command, capture_output=True)
                if output:
                    print(output)
        except KeyboardInterrupt:
            self.log("Log tailing stopped", "INFO")
    
    def get_helm_releases(self, environment: str, namespace: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get Helm releases for the environment"""
        if namespace is None:
            namespace = environment
        
        command = ["helm", "list", "-n", namespace, "-o", "json"]
        output = self.run_command(command, capture_output=True)
        
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                self.log("Failed to parse Helm releases", "ERROR")
        return None
    
    def get_helm_history(self, environment: str, namespace: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get Helm release history"""
        if namespace is None:
            namespace = environment
        
        command = ["helm", "history", self.app_name, "-n", namespace, "-o", "json"]
        output = self.run_command(command, capture_output=True)
        
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                self.log("Failed to parse Helm history", "ERROR")
        return None
    
    def rollback_release(self, environment: str, revision: Optional[int] = None, 
                        confirm: bool = False, namespace: Optional[str] = None) -> None:
        """Rollback Helm release to previous or specific revision"""
        if not self.validate_environment(environment):
            return
        
        if namespace is None:
            namespace = environment
        
        self.log(f"Initiating rollback for {self.app_name} in {environment} environment")
        
        # Update kubeconfig
        if not self.update_kubeconfig(environment):
            return
        
        # Get current release information
        releases = self.get_helm_releases(environment, namespace)
        if not releases:
            self.log("No Helm releases found", "ERROR")
            return
        
        app_release = None
        for release in releases:
            if release["name"] == self.app_name:
                app_release = release
                break
        
        if not app_release:
            self.log(f"Helm release '{self.app_name}' not found", "ERROR")
            return
        
        current_revision = app_release["revision"]
        self.log(f"Current revision: {current_revision}")
        
        # Get history
        history = self.get_helm_history(environment, namespace)
        if not history:
            self.log("Could not get release history", "ERROR")
            return
        
        if len(history) < 2 and revision is None:
            self.log("No previous revisions available for rollback", "ERROR")
            return
        
        # Determine target revision
        if revision is None:
            # Find previous revision
            sorted_history = sorted(history, key=lambda x: x["revision"], reverse=True)
            if len(sorted_history) >= 2:
                target_revision = sorted_history[1]["revision"]
            else:
                self.log("No previous revision found", "ERROR")
                return
        else:
            target_revision = revision
            # Validate revision exists
            valid_revisions = [h["revision"] for h in history]
            if target_revision not in valid_revisions:
                self.log(f"Revision {target_revision} not found. Available: {valid_revisions}", "ERROR")
                return
        
        self.log(f"Target revision: {target_revision}")
        
        # Show rollback details
        target_history = next((h for h in history if h["revision"] == target_revision), None)
        if target_history:
            self.log(f"Rolling back to: {target_history['description']}")
            self.log(f"Updated: {target_history['updated']}")
        
        # Confirm rollback
        if not confirm:
            try:
                response = input(f"{Colors.YELLOW}Proceed with rollback? (y/N): {Colors.RESET}")
                if response.lower() != 'y':
                    self.log("Rollback cancelled", "WARNING")
                    return
            except KeyboardInterrupt:
                self.log("Operation cancelled", "WARNING")
                return
        
        # Perform rollback
        command = ["helm", "rollback", self.app_name, str(target_revision), "-n", namespace]
        
        self.log(f"Executing rollback...")
        if self.run_command(command) is not None:
            self.log("Rollback initiated successfully", "SUCCESS")
            
            # Wait for deployment to be ready
            self.log("Waiting for deployment to be ready...")
            wait_command = [
                "kubectl", "rollout", "status", f"deployment/{self.app_name}",
                "-n", namespace, "--timeout=300s"
            ]
            
            if self.run_command(wait_command) is not None:
                self.log("Rollback completed successfully", "SUCCESS")
                
                # Show current pods
                pods = self.get_pods(environment, namespace)
                if pods:
                    self.log("Current pods:")
                    for pod in pods:
                        name = pod["metadata"]["name"]
                        status = pod["status"]["phase"]
                        self.log(f"  {name}: {status}")
            else:
                self.log("Rollback may have failed - check deployment status", "WARNING")
        else:
            self.log("Rollback failed", "ERROR")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="DevOps CLI Tool for EKS Sample Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Tail logs from dev environment
  python dev-cli.py logs --environment dev --follow

  # Show last 50 lines of logs
  python dev-cli.py logs --environment prod --lines 50

  # Rollback to previous release in staging
  python dev-cli.py rollback --environment stage

  # Rollback to specific revision with confirmation
  python dev-cli.py rollback --environment prod --revision 3 --confirm

  # Get help for specific command
  python dev-cli.py logs --help
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Tail application logs")
    logs_parser.add_argument("-e", "--environment", required=True, 
                           choices=["dev", "stage", "prod"],
                           help="Target environment")
    logs_parser.add_argument("-f", "--follow", action="store_true",
                           help="Follow log output")
    logs_parser.add_argument("-l", "--lines", type=int, default=100,
                           help="Number of lines to show (default: 100)")
    logs_parser.add_argument("-p", "--pod", 
                           help="Specific pod name (optional)")
    logs_parser.add_argument("-n", "--namespace",
                           help="Kubernetes namespace (defaults to environment)")
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback Helm release")
    rollback_parser.add_argument("-e", "--environment", required=True,
                               choices=["dev", "stage", "prod"],
                               help="Target environment")
    rollback_parser.add_argument("-r", "--revision", type=int,
                               help="Specific revision to rollback to (optional)")
    rollback_parser.add_argument("-c", "--confirm", action="store_true",
                               help="Skip confirmation prompt")
    rollback_parser.add_argument("-n", "--namespace",
                               help="Kubernetes namespace (defaults to environment)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = DevOpsCLI()
    
    try:
        if args.command == "logs":
            cli.tail_logs(
                environment=args.environment,
                follow=args.follow,
                lines=args.lines,
                pod_name=args.pod,
                namespace=args.namespace
            )
        elif args.command == "rollback":
            cli.rollback_release(
                environment=args.environment,
                revision=args.revision,
                confirm=args.confirm,
                namespace=args.namespace
            )
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation interrupted{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
