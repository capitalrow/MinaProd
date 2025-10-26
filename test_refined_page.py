"""
Test script to verify refined page data flow
"""
import logging
from app import app
from flask import url_for

logging.basicConfig(level=logging.INFO)

def test_refined_page():
    """Test the refined page route with session 209"""
    with app.test_client() as client:
        with app.app_context():
            # Test with external_id
            external_id = "1761505477403"
            response = client.get(f'/sessions/{external_id}/refined')
            
            print(f"\n{'='*80}")
            print(f"Testing /sessions/{external_id}/refined")
            print(f"{'='*80}")
            print(f"Status Code: {response.status_code}")
            print(f"Content Length: {len(response.data)} bytes")
            
            if response.status_code == 200:
                content = response.data.decode('utf-8')
                
                # Check for key elements
                checks = {
                    'Summary section': 'Full Transcript' in content,
                    'Highlights tab': 'Highlights' in content,
                    'Analytics tab': 'Analytics' in content,
                    'Tasks tab': 'Tasks' in content,
                    'Tab switching JS': 'switchTab' in content,
                    'Analytics data': 'word_count' in content.lower() or 'total words' in content.lower(),
                }
                
                print(f"\n{'='*80}")
                print(f"Content Checks:")
                print(f"{'='*80}")
                for check_name, result in checks.items():
                    status = "✅" if result else "❌"
                    print(f"{status} {check_name}: {result}")
                
                # Check if summary data is present
                if 'Insights are still being generated' in content:
                    print(f"\n⚠️ Empty state shown for insights (summary not available)")
                elif 'summary_md' in content.lower() or 'no key highlights identified' in content.lower():
                    print(f"\n✅ Summary data template present")
                
                print(f"\n{'='*80}")
                print(f"Test Result: {'PASSED ✅' if response.status_code == 200 else 'FAILED ❌'}")
                print(f"{'='*80}\n")
                
            else:
                print(f"❌ FAILED: Status code {response.status_code}")
                print(f"Response: {response.data.decode('utf-8')[:500]}")

if __name__ == "__main__":
    test_refined_page()
