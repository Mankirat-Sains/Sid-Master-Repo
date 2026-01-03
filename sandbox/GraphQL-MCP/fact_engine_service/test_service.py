#!/usr/bin/env python3
"""Test script for Fact Engine Service"""
import requests
import json
import sys
import argparse
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("⚠️  IMPORTANT: Viewing Logs")
print("=" * 80)
print()
print("The detailed logs (PLANNER, EXECUTOR, COMPOSER) appear in the")
print("TERMINAL WHERE THE SERVICE IS RUNNING, not in this test script!")
print()
print("To see the logs:")
print("  1. Make sure the service is running in another terminal:")
print("     cd fact_engine_service")
print("     python main.py")
print()
print("  2. Keep that terminal visible - that's where you'll see:")
print("     - PLANNER: logs showing the FactPlan generation")
print("     - EXECUTOR: logs showing candidate discovery and fact extraction")
print("     - COMPOSER: logs showing answer composition")
print("     - MAIN: logs showing the overall pipeline flow")
print()
print("  3. If you don't see logs, the service may need to be restarted")
print("     to pick up the new logging code.")
print()
print("=" * 80)
print()


def test_health() -> bool:
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        data = response.json()
        print("✅ Health Check:")
        print(f"   Status: {data.get('status')}")
        print(f"   Components: {json.dumps(data.get('components', {}), indent=6)}")
        return response.status_code == 200 and data.get("status") == "healthy"
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_facts() -> bool:
    """Test facts endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/facts", timeout=30)
        data = response.json()
        print("\n✅ Available Facts:")
        for fact in data.get("available_facts", []):
            print(f"   - {fact}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Facts endpoint failed: {e}")
        return False


def test_query(question: str, verbose: bool = True) -> Dict[str, Any]:
    """Test a query"""
    try:
        if verbose:
            print(f"\n📝 Question: {question}")
        
        response = requests.post(
            f"{BASE_URL}/query",
            json={"question": question},
            timeout=60  # Queries can take time
        )
        
        if response.status_code != 200:
            print(f"❌ Query failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return {}
        
        data = response.json()
        
        if verbose:
            answer = data.get("answer", {})
            fact_result = data.get("fact_result", {})
            
            answer_text = answer.get('answer', 'N/A')
            # Show full answer if short, otherwise truncate with indication
            if len(answer_text) > 200:
                print(f"✅ Answer: {answer_text[:200]}...")
                print(f"   (Full answer length: {len(answer_text)} chars)")
            else:
                print(f"✅ Answer: {answer_text}")
            print(f"   Confidence: {answer.get('confidence', 0):.2f}")
            print(f"   Projects: {answer.get('project_count', 0)}")
            print(f"   Execution Time: {fact_result.get('execution_time_ms', 0):.1f}ms")
            print(f"   Elements Processed: {fact_result.get('total_elements_processed', 0)}")
            
            if answer.get('supporting_facts'):
                print(f"   Supporting Facts: {len(answer['supporting_facts'])}")
            
            # Show fact_result summary if available
            if fact_result.get('projects'):
                print(f"   Projects in result: {len(fact_result['projects'])}")
                for pid, proj in list(fact_result['projects'].items())[:3]:
                    print(f"     - {proj.get('project_name', pid)}: {len(proj.get('elements', {}))} element types")
        
        return data
    except requests.exceptions.Timeout:
        print(f"❌ Query timed out (may be processing large dataset)")
        return {}
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return {}


def run_single_query(question: str):
    """Run a single query interactively"""
    print("=" * 80)
    print("Fact Engine Service - Single Query Test")
    print("=" * 80)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Service is not healthy. Please check the service is running.")
        sys.exit(1)
    
    # Test 2: Facts endpoint
    test_facts()
    
    # Test 3: Run the query
    print("\n" + "=" * 80)
    print("Running Query")
    print("=" * 80)
    print(f"\n📝 Question: {question}")
    print("\n⏳ Sending query to service...")
    print("   (Check the service terminal for detailed logs)")
    print()
    
    result = test_query(question, verbose=True)
    
    if result:
        print("\n✅ Query completed successfully!")
        return True
    else:
        print("\n❌ Query failed!")
        return False


def run_all_tests():
    """Run all test cases"""
    print("=" * 60)
    print("Fact Engine Service - Test Suite")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Service is not healthy. Please check the service is running.")
        sys.exit(1)
    
    # Test 2: Facts endpoint
    test_facts()
    
    # Test 3: Simple queries
    print("\n" + "=" * 60)
    print("Testing Queries")
    print("=" * 60)
    
    test_cases = [
        "Do we have any timber columns?",
        "What materials are used in our projects?",
        "How many steel beams are there?",
        "What types of structural elements do we have?",
    ]
    
    results = []
    for question in test_cases:
        result = test_query(question)
        results.append({
            "question": question,
            "success": bool(result),
            "has_answer": bool(result.get("answer"))
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for r in results if r["success"])
    print(f"Passed: {passed}/{len(results)}")
    
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"{status} {r['question']}")
    
    return passed == len(results)


def run_interactive():
    """Run queries interactively"""
    print("=" * 80)
    print("Fact Engine Service - Interactive Query Mode")
    print("=" * 80)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Service is not healthy. Please check the service is running.")
        sys.exit(1)
    
    # Test 2: Facts endpoint
    test_facts()
    
    # Test 3: Interactive queries
    print("\n" + "=" * 80)
    print("Interactive Query Mode")
    print("=" * 80)
    print("\nEnter questions one at a time. Type 'quit' or 'exit' to stop.")
    print("(Check the service terminal for detailed logs)")
    print()
    
    while True:
        try:
            question = input("\n📝 Enter your question (or 'quit' to exit): ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not question:
                print("Please enter a question.")
                continue
            
            print(f"\n⏳ Processing: {question}")
            print("   (Check the service terminal for detailed logs)")
            print()
            
            result = test_query(question, verbose=True)
            
            if result:
                print("\n✅ Query completed!")
            else:
                print("\n❌ Query failed!")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Fact Engine Service")
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Run a single question"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode (one question at a time)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all test cases"
    )
    
    args = parser.parse_args()
    
    if args.question:
        success = run_single_query(args.question)
        sys.exit(0 if success else 1)
    elif args.interactive:
        run_interactive()
        sys.exit(0)
    elif args.all:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    else:
        # Default: interactive mode
        run_interactive()
        sys.exit(0)

