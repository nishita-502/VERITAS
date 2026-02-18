# from src.agents.graph import build_workflow

# app = build_workflow()
# inputs = {"question": "Does the candidate know Python?"}
# for output in app.stream(inputs):
#     print(output)

from src.agents.graph import build_workflow
import sys

def run_veritas():
    # 1. Compile the Graph
    app = build_workflow()
    
    print("\n" + "="*50)
    print("🕵️‍♂️ VERITAS: THE SMART RECRUITER AGENT")
    print("Type 'exit' or 'quit' to stop the session.")
    print("="*50 + "\n")

    while True:
        # 2. Get User Input
        user_query = input("👉 Enter your query: ").strip()

        if user_query.lower() in ["exit", "quit"]:
            print("Goodbye! Ending session.")
            break
        
        if not user_query:
            continue

        # 3. Prepare State Input
        inputs = {"question": user_query}

        # 4. Stream the Graph Execution
        print("\n--- AGENT THINKING PROCESS ---")
        final_output = None
        
        for output in app.stream(inputs):
            for key, value in output.items():
                print(f"📍 Node completed: [{key.upper()}]")
                # Store the last output to display the final result
                final_output = value

        # 5. Display the Final Result and Trust Score
        if final_output and "generation" in final_output:
            print("\n" + "-"*30)
            print("📝 VERITAS RESPONSE:")
            print(final_output["generation"])
            
            if "trust_score" in final_output:
                ts = final_output["trust_score"]
                print(f"\n✅ TRUST SCORE: {ts['score']}/100")
                print(f"📊 LABEL: {ts['label']}")
                print(f"💡 REASONING: {ts['reasoning']}")
            print("-"*30 + "\n")

if __name__ == "__main__":
    try:
        run_veritas()
    except KeyboardInterrupt:
        print("\nSession interrupted by user. Closing...")
        sys.exit(0)