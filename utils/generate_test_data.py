#!/usr/bin/env python3

import json
import random
import requests
import string
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import argparse
from colorama import init
from termcolor import colored

# Initialize colorama for Windows support
init()

# Configuration
BASE_URL = "http://localhost:8080"
NUM_CASES = 10
EVENTS_PER_CASE = 10

# Emoji constants
EMOJIS = {
    "understand_the_complaint": "📄",
    "investigate_and_data_gather": "🔎",
    "find_relevant_info": "📚",
    "contact_customer": "📞",
    "send_payment": "💰",
    "problem_fix": "🛠️",
    "generate_frl": "📩",
    "close_case": "🔒"
}

STATUS_EMOJIS = {
    "success": "✅",
    "error": "❌",
    "info": "ℹ️",
    "warning": "⚠️",
    "start": "🚀",
    "complete": "🏁",
    "processing": "⚙️"
}

# Event types and their possible metadata
EVENT_TYPES = list(EMOJIS.keys())

METADATA_TEMPLATES = {

    "understand_the_complaint": {
        "system": ["nucleus", "merlin"]
    },

    "investigate_and_data_gather": {
        "system": ["pega", "visionplus", "cobra", "mainframe", "ocis", "ewfm"]
    },
    
    "find_relevant_info": {
        "system": ["knowledgehub", "athena", "fountain", "verint", "merlin"]
    },

    "contact_customer": {
        "system": ["o2portal", "avaya", "verint"]
    },
    
    "send_payment": {
        "system": ["nucleus", "pega"]
    }, 

    "problem_fix": {
        "system": ["nucleus", "pega", "visionplus", "cobra"]
    },

    "generate_frl": {
        "system": "smartcomms"
    },
    
    "close_case": {
        "system": "nucleus"
    },       
}

def log_info(message: str, emoji: str = "ℹ️", color: str = "white") -> None:
    """Print a colorful log message with an emoji."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{emoji} {colored(timestamp, 'cyan')} | {colored(message, color)}")

def log_success(message: str) -> None:
    """Print a success message."""
    log_info(message, STATUS_EMOJIS["success"], "green")

def log_error(message: str) -> None:
    """Print an error message."""
    log_info(message, STATUS_EMOJIS["error"], "red")

def log_warning(message: str) -> None:
    """Print a warning message."""
    log_info(message, STATUS_EMOJIS["warning"], "yellow")

def generate_case_id() -> str:
    """Generate a random case ID."""
    prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
    number = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{number}"

def generate_metadata(event_type: str) -> Dict:
    """Generate random metadata for a given event type."""
    template = METADATA_TEMPLATES[event_type]
    metadata = {}
    
    for key, values in template.items():
        if isinstance(values, range):
            metadata[key] = random.choice(list(values))
        else:
            metadata[key] = random.choice(values)
    
    return metadata

def create_event(case_id: str, fileid: int, product: str, workstream: str, event_number: int, event_timestamp: datetime) -> List[Dict]:
    """Create a pair of start and end events for a case."""
    event_type = random.choice(EVENT_TYPES)
    
    # Generate a random duration between 1 hour and 4 hours
    # For certain event types, use longer durations
    if event_type in ["client_meeting", "document_review", "case_update"]:
        duration_minutes = random.randint(120, 240)  # 2-4 hours
    else:
        duration_minutes = random.randint(60, 180)  # 1-3 hours
    
    # Create start event with the given timestamp
    start_event = {
        "case_id": case_id,
        "product": product,
        "workstream": workstream,
        "fileid": fileid,
        "event_name": event_type,
        "event_type": "start",
        "metadata": generate_metadata(event_type),
        "timestamp": event_timestamp.isoformat()
    }
    
    # Create end event with timestamp + duration
    end_event = {
        "case_id": case_id,
        "product": product,
        "workstream": workstream,
        "fileid": fileid,
        "event_name": event_type,
        "event_type": "end",
        "metadata": generate_metadata(event_type),
        "timestamp": (event_timestamp + timedelta(minutes=duration_minutes)).isoformat()
    }
    
    return [start_event, end_event]

def generate_case_events(case_number: int) -> List[Dict]:
    """Generate all events for a single case."""
    case_id = generate_case_id()
    product = random.choice(["PCA", "Mortgages", "Loans", "Savings"])
    if product == "PCA":
        workstream = random.choice["PCA BAU", "PCA C&R", "PCA F&D"]
    elif product == "Mortgages":
        workstream = random.choice["Mortgages BAU", "Mortgages C&R", "Mortgages F&D"]
    elif product == "Loans":
        workstream = random.choice["Loans BAU", "Loans C&R", "Loans F&D"]
    elif product == "Savings":
        workstream = random.choice["Savings BAU", "Savings C&R", "Savings F&D"]
    fileid = random.randint(7803225, 7803235)
    events = []
    
    # Generate a random start time within the last 30 days
    current_time = datetime.now()
    case_start_time = current_time - timedelta(days=random.randint(1, 30))
    
    log_info(f"Starting case {case_number + 1}/{NUM_CASES} with ID: {case_id}", "📝", "blue")
    
    for event_number in range(EVENTS_PER_CASE):
        # Add random time between events (minimum 1 hour)
        if event_number > 0:
            # Get the end time of the previous event
            prev_event_end = datetime.fromisoformat(events[-1]["timestamp"])
            # Ensure at least 1 hour gap between events
            # For certain event types, use longer gaps
            if events[-1]["event_name"] in ["client_meeting", "document_review"]:
                gap_minutes = random.randint(120, 180)  # 2-3 hours
            else:
                gap_minutes = random.randint(60, 120)  # 1-2 hours
            case_start_time = prev_event_end + timedelta(minutes=gap_minutes)
        
        # Create both start and end events
        event_pair = create_event(case_id, fileid, product, workstream, event_number, case_start_time)
        events.extend(event_pair)
        
        # Add small random delay between event generation
        time.sleep(random.uniform(0.1, 0.3))
        
        event_emoji = EMOJIS[event_pair[0]["event_name"]]
        start_time = datetime.fromisoformat(event_pair[0]["timestamp"])
        end_time = datetime.fromisoformat(event_pair[1]["timestamp"])
        duration = (end_time - start_time).total_seconds() / 60  # Convert to minutes
        
        log_info(
            f"Generated event pair {event_number + 1}/{EVENTS_PER_CASE} for case {case_id}: "
            f"{event_emoji} {event_pair[0]['event_name']} "
            f"(Duration: {duration:.1f} minutes)",
            STATUS_EMOJIS["processing"],
            "blue"
        )
    
    log_success(f"Completed case {case_number + 1}/{NUM_CASES}: {case_id}")
    return events

def post_event(event: Dict) -> bool:
    """Post a single event to the API."""
    try:
        event_emoji = EMOJIS[event["event_name"]]
        log_info(
            f"Posting event: {event_emoji} {event['event_name']} for case {event['case_id']}",
            "📤",
            "cyan"
        )
        
        response = requests.post(f"{BASE_URL}/events", json=event)
        response.raise_for_status()
        
        log_success(f"Successfully posted event for case {event['case_id']}")
        return True
    except requests.exceptions.RequestException as e:
        log_error(f"Error posting event for case {event['case_id']}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate test data for event tracking system')
    parser.add_argument('--dry-run', action='store_true', help='Only print events without sending to API')
    parser.add_argument('--output', type=str, help='Save events to JSON file instead of sending to API')
    args = parser.parse_args()

    start_time = datetime.now()
    log_info("Starting data generation", STATUS_EMOJIS["start"], "magenta")
    
    all_events = []
    case_ids = set()  # Track unique case IDs
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        case_events = list(executor.map(generate_case_events, range(NUM_CASES)))
        for events in case_events:
            # Verify case IDs are unique
            for event in events:
                case_ids.add(event["case_id"])
            all_events.extend(events)

    # Verify we have the expected number of unique case IDs
    if len(case_ids) != NUM_CASES:
        log_warning(f"Warning: Expected {NUM_CASES} unique case IDs, but got {len(case_ids)}")
        log_info("Case IDs generated:", "🔍", "yellow")
        for case_id in sorted(case_ids):
            log_info(f"  {case_id}", "📝", "yellow")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(all_events, f, indent=2)
        log_success(f"Events saved to {args.output}")
    elif args.dry_run:
        print("\n" + "="*50)
        print(colored("Sample Events (first 5):", "yellow"))
        print("="*50 + "\n")
        print(json.dumps(all_events[:5], indent=2))
        log_info(f"Generated {len(all_events)} events (dry run)", "🔍", "yellow")
    else:
        log_info("Posting events to API...", "📤", "cyan")
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(post_event, all_events))
        
        success_count = sum(results)
        if success_count == len(all_events):
            log_success(f"Successfully posted all {success_count} events!")
        else:
            log_warning(
                f"Posted {success_count} out of {len(all_events)} events "
                f"({len(all_events) - success_count} failed)"
            )

    end_time = datetime.now()
    duration = end_time - start_time
    log_info(
        f"Completed in {duration.total_seconds():.2f} seconds",
        STATUS_EMOJIS["complete"],
        "magenta"
    )

if __name__ == "__main__":
    main() 