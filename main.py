import asyncio
import json
import sys
from pathlib import Path

from config import ensure_directories
from orchestrator import DealFlowOrchestrator
from services.database_services import DatabaseService
from services.storage_services import StorageService
from utils.transcript_parser import TranscriptParser
async def main():
    ensure_directories()

    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_fireflies_json>")
        print("       python main.py --sample  (to use sample transcript)")
        sys.exit(1)

    if sys.argv[1] == "--sample":
        sample_path = Path(__file__).parent.parent / "user_input_files" / "pasted-text-2026-05-27T12-13-25.txt"
        if sample_path.exists():
            with open(sample_path) as f:
                raw_json = json.load(f)
        else:
            print("Sample file not found")
            sys.exit(1)
    else:
        input_path = Path(sys.argv[1])
        with open(input_path) as f:
            raw_json = json.load(f)

    print(f"Processing transcript: {raw_json.get('meeting_id', 'unknown')}")
    print(f"Title: {raw_json.get('title', 'unknown')}")

    orchestrator = DealFlowOrchestrator()

    print("Executing Layer 1 (Extractor + Taskmage in parallel)...")
    result = await orchestrator.process_transcript(raw_json)

    if result.get("agent_2_tickets"):
        orchestrator.save_tasks_to_database(result["agent_2_tickets"], result["metadata"]["meeting_id"])
        print(f"Saved {len(result['agent_2_tickets'].get('tasks', []))} tasks to database")

    print("\n=== RESULTS ===\n")

    print("--- AGENT 1: EXTRACTION ---")
    print(json.dumps(result.get("agent_1_extraction", {}), indent=2))

    print("\n--- AGENT 2: TASKS ---")
    print(json.dumps(result.get("agent_2_tickets", {}), indent=2))

    print("\n--- AGENT 3: HUBSPOT ---")
    print(json.dumps(result.get("agent_3_hubspot", {}), indent=2))

    print("\n--- AGENT 4: EMAIL ---")
    print(json.dumps(result.get("agent_4_email", {}), indent=2))

    storage = StorageService()
    output_path = storage.save_full_output(result, result["metadata"]["meeting_id"])
    print(f"\nFull output saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())