import asyncio
import json
import sys
from pathlib import Path

from core.config import ensure_directories
from core.orchestrator import DealFlowOrchestrator
from services.storage_services import StorageService


async def main():
    ensure_directories()

    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_fireflies_json>")
        print("       python main.py --sample")
        sys.exit(1)

    if sys.argv[1] == "--sample":
        sample_path = Path(__file__).parent.parent / "user_input_files" / "pasted-text-2026-05-27T12-13-25.txt"
        if not sample_path.exists():
            print("Sample file not found")
            sys.exit(1)
        raw_json = json.loads(sample_path.read_text())
    else:
        raw_json = json.loads(Path(sys.argv[1]).read_text())

    print(f"Processing: {raw_json.get('meeting_id', 'unknown')} — {raw_json.get('title', 'unknown')}")

    result = await DealFlowOrchestrator().process_transcript(raw_json)

    print("\n=== RESULTS ===\n")
    print("--- AGENT 1: EXTRACTION ---")
    print(json.dumps(result.get("agent_1_extraction", {}), indent=2))
    print("\n--- AGENT 2: TASKS ---")
    print(json.dumps(result.get("agent_2_tickets", {}), indent=2))
    print("\n--- AGENT 3: HUBSPOT ---")
    print(json.dumps(result.get("agent_3_hubspot", {}), indent=2))
    print("\n--- AGENT 4: EMAIL ---")
    print(json.dumps(result.get("agent_4_email", {}), indent=2))

    output_path = StorageService().save_full_output(result, result["metadata"]["meeting_id"])
    print(f"\nFull output saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
