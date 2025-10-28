"""
Manual Validation Script for Tasks Page Features
Run this script while the application is running to validate key functionality
"""
import requests
import json
import time
from typing import Dict, List

BASE_URL = "http://localhost:5000"

class TasksValidator:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_task_ids = []
        
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log a test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
        print(f"{status} - {test_name}")
        if message:
            print(f"    {message}")
    
    def test_create_manual_task(self) -> bool:
        """Test creating a task without meeting association"""
        print("\n=== Testing Manual Task Creation ===")
        
        task_data = {
            'title': f'Manual Test Task {int(time.time())}',
            'description': 'Created by validation script',
            'priority': 'high',
            'status': 'todo'
        }
        
        try:
            response = self.session.post(
                f'{BASE_URL}/api/tasks',
                json=task_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                data = response.json()
                task_id = data.get('task', {}).get('id')
                if task_id:
                    self.created_task_ids.append(task_id)
                
                self.log_result(
                    "Create Manual Task",
                    True,
                    f"Task created with ID: {task_id}"
                )
                return True
            elif response.status_code == 401:
                self.log_result(
                    "Create Manual Task",
                    False,
                    "Authentication required - please login first"
                )
                return False
            else:
                self.log_result(
                    "Create Manual Task",
                    False,
                    f"Unexpected status code: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Create Manual Task",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_get_all_tasks(self) -> bool:
        """Test retrieving all tasks"""
        print("\n=== Testing Task Retrieval ===")
        
        try:
            response = self.session.get(f'{BASE_URL}/api/tasks')
            
            if response.status_code == 200:
                data = response.json()
                task_count = len(data.get('tasks', []))
                self.log_result(
                    "Get All Tasks",
                    True,
                    f"Retrieved {task_count} tasks"
                )
                return True
            elif response.status_code == 401:
                self.log_result(
                    "Get All Tasks",
                    False,
                    "Authentication required"
                )
                return False
            else:
                self.log_result(
                    "Get All Tasks",
                    False,
                    f"Status code: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Get All Tasks",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_update_task(self) -> bool:
        """Test updating a task (inline edit simulation)"""
        print("\n=== Testing Task Update ===")
        
        if not self.created_task_ids:
            self.log_result(
                "Update Task",
                False,
                "No task ID available to update"
            )
            return False
        
        task_id = self.created_task_ids[0]
        update_data = {
            'title': f'Updated Task Title {int(time.time())}',
            'priority': 'urgent'
        }
        
        try:
            response = self.session.put(
                f'{BASE_URL}/api/tasks/{task_id}',
                json=update_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                updated_title = data.get('task', {}).get('title')
                self.log_result(
                    "Update Task",
                    True,
                    f"Task updated to: {updated_title}"
                )
                return True
            else:
                self.log_result(
                    "Update Task",
                    False,
                    f"Status code: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Update Task",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_toggle_completion(self) -> bool:
        """Test marking task as complete"""
        print("\n=== Testing Task Completion Toggle ===")
        
        if not self.created_task_ids:
            self.log_result(
                "Toggle Completion",
                False,
                "No task ID available"
            )
            return False
        
        task_id = self.created_task_ids[0]
        
        try:
            # Mark as complete
            response = self.session.put(
                f'{BASE_URL}/api/tasks/{task_id}',
                json={'status': 'completed'},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('task', {}).get('status')
                self.log_result(
                    "Toggle Completion",
                    status == 'completed',
                    f"Task status: {status}"
                )
                return status == 'completed'
            else:
                self.log_result(
                    "Toggle Completion",
                    False,
                    f"Status code: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Toggle Completion",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_delete_task(self) -> bool:
        """Test deleting a task"""
        print("\n=== Testing Task Deletion ===")
        
        if not self.created_task_ids:
            self.log_result(
                "Delete Task",
                False,
                "No task ID available to delete"
            )
            return False
        
        task_id = self.created_task_ids.pop()
        
        try:
            response = self.session.delete(f'{BASE_URL}/api/tasks/{task_id}')
            
            if response.status_code == 200:
                self.log_result(
                    "Delete Task",
                    True,
                    f"Task {task_id} deleted successfully"
                )
                return True
            elif response.status_code == 404:
                self.log_result(
                    "Delete Task",
                    False,
                    "Task not found"
                )
                return False
            else:
                self.log_result(
                    "Delete Task",
                    False,
                    f"Status code: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Delete Task",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test that tasks API endpoints exist"""
        print("\n=== Testing API Endpoints ===")
        
        endpoints = [
            ('GET', '/api/tasks'),
            ('POST', '/api/tasks'),
        ]
        
        all_exist = True
        for method, endpoint in endpoints:
            try:
                if method == 'GET':
                    response = self.session.get(f'{BASE_URL}{endpoint}')
                else:
                    response = self.session.post(
                        f'{BASE_URL}{endpoint}',
                        json={'title': 'Test'}
                    )
                
                # Accept any response that's not 404 (endpoint exists)
                exists = response.status_code != 404
                self.log_result(
                    f"Endpoint {method} {endpoint}",
                    exists,
                    f"Status: {response.status_code}"
                )
                all_exist = all_exist and exists
                
            except Exception as e:
                self.log_result(
                    f"Endpoint {method} {endpoint}",
                    False,
                    f"Error: {str(e)}"
                )
                all_exist = False
        
        return all_exist
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "="*60)
        
        if pass_rate == 100:
            print("🎉 ALL TESTS PASSED! Tasks page is working correctly.")
        elif pass_rate >= 80:
            print("⚠️  Most tests passed, but some features need attention.")
        else:
            print("❌ Many tests failed. Please check the implementation.")
        
        print("="*60 + "\n")


def main():
    """Run all validation tests"""
    print("="*60)
    print("TASKS PAGE MANUAL VALIDATION")
    print("="*60)
    print("\nℹ️  Make sure:")
    print("  1. The application is running at http://localhost:5000")
    print("  2. You are logged in (or tests will fail with 401)")
    print("\n" + "-"*60)
    
    validator = TasksValidator()
    
    # Run tests in sequence
    validator.test_api_endpoints()
    validator.test_create_manual_task()
    validator.test_get_all_tasks()
    validator.test_update_task()
    validator.test_toggle_completion()
    validator.test_delete_task()
    
    # Print summary
    validator.print_summary()


if __name__ == "__main__":
    main()
