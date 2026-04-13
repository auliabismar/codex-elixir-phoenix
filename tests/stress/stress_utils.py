import re
import random
import time
import xml.sax.saxutils as saxutils

class MockAgentFactory:
    @staticmethod
    def get_response(role: str, behavior: str = "success") -> str:
        if behavior == "slow":
            time.sleep(random.uniform(1.0, 3.0))
        
        if behavior == "malformed":
            return f'<discovery role="{role}">\nUnclosed tag here...'
        
        if behavior == "success":
            return f"Mocked discovery content for {role}."
        
        return ""

class AuditPlan:
    @staticmethod
    def check_integrity(plan_md_content: str) -> dict:
        issues = []
        
        # Check for duplicate tasks
        tasks_section = re.search(r"## Tasks\s*\n\n(.*?)(?=##|$)", plan_md_content, re.DOTALL)
        if tasks_section:
            task_lines = [line.strip() for line in tasks_section.group(1).splitlines() if line.strip()]
            if len(task_lines) != len(set(task_lines)):
                issues.append("Duplicate task entries found.")
        
        # Check for truncated XML blocks in notes/aggregated context
        if "<discovery" in plan_md_content and "</discovery>" not in plan_md_content:
            issues.append("Potential truncated XML discovery block.")
            
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
