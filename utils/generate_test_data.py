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
import numpy as np

# Initialize colorama for Windows support
init()

# Configuration
BASE_URL = "http://localhost:8080"
NUM_CASES = 10
EVENTS_PER_CASE = 10

# Emoji constants
EMOJIS = {
    "understand_the_complaint": "🎯",
    "investigate_and_data_gather": "🔍",
    "find_relevant_info": "📚",
    "contact_customer": "📞",
    "send_payment": "💰",
    "problem_fix": "🔧",
    "generate_frl": "📄",
    "close_case": "✅"
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
        "system": ["nucleus", "merlin"],
        "priority": ["high", "medium", "low"],
        "category": ["billing", "technical", "service", "account"]
    },
    "investigate_and_data_gather": {
        "system": ["pega", "visionplus", "cobra", "mainframe", "ocis", "ewfm"],
        "data_type": ["customer_info", "billing_history", "service_records", "technical_logs"],
        "complexity": ["simple", "moderate", "complex"]
    },
    "find_relevant_info": {
        "system": ["knowledgehub", "athena", "fountain", "verint", "merlin"],
        "info_type": ["policies", "procedures", "historical_cases", "documentation"],
        "relevance": ["high", "medium", "low"]
    },
    "contact_customer": {
        "system": ["o2portal", "avaya", "verint"],
        "contact_method": ["phone", "email", "chat"],
        "outcome": ["successful", "voicemail", "reschedule", "no_answer"]
    },
    "send_payment": {
        "system": ["nucleus", "pega"],
        "amount": range(10, 10001),
        "payment_type": ["refund", "compensation", "adjustment"],
        "status": ["processed", "pending", "failed"]
    },
    "problem_fix": {
        "system": ["nucleus", "pega", "visionplus", "cobra"],
        "fix_type": ["technical", "billing", "service", "account"],
        "resolution": ["resolved", "partial", "escalated"]
    },
    "generate_frl": {
        "system": ["smartcomms"],
        "document_type": ["resolution_letter", "explanation_letter", "apology_letter"],
        "priority": ["high", "medium", "low"]
    },
    "close_case": {
        "system": ["nucleus"],
        "closure_type": ["resolved", "escalated", "transferred"],
        "satisfaction_level": ["high", "medium", "low"]
    }
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
        
    metadata["product"] = random.choice(["PCA", "Mortgages", "Loans", "Savings"])
    if metadata["product"] == "PCA":
        metadata["workstream"] = random.choice(["PCA BAU", "PCA C&R", "PCA F&D"])
    elif metadata["product"] == "Mortgages":
        metadata["workstream"] = random.choice(["Mortgages BAU", "Mortgages C&R", "Mortgages F&D"])
    elif metadata["product"] == "Loans":
        metadata["workstream"] = random.choice(["Loans BAU", "Loans C&R", "Loans F&D"])
    elif metadata["product"] == "Savings":
        metadata["workstream"] = random.choice(["Savings BAU", "Savings C&R", "Savings F&D"])
    metadata["fileid"] = random.randint(7803225, 7803235)
    
    return metadata

def create_event(case_id: str, event_number: int, event_timestamp: datetime) -> List[Dict]:
    """Create a pair of start and end events for a case."""
    event_type = random.choice(EVENT_TYPES)

    event_index = EVENT_TYPES.index(event_type)
    # Proportion of average time taken by each event type in the whole case
    prop = [8, 23, 12, 6, 4, 9, 19, 9]
    # Generate a duration in minutes following a normal distribution
    duration_minutes = np.random.normal(180, 30) * (prop[event_index] / sum(prop))
    
    # Create start event with the given timestamp
    start_event = {
        "case_id": case_id,
        "event_name": event_type,
        "event_type": "start",
        "metadata": generate_metadata(event_type),
        "timestamp": event_timestamp.isoformat()
    }
    
    # Create end event with timestamp + duration
    end_event = {
        "case_id": case_id,
        "event_name": event_type,
        "event_type": "end",
        "metadata": generate_metadata(event_type),
        "timestamp": (event_timestamp + timedelta(minutes=duration_minutes)).isoformat()
    }
    
    return [start_event, end_event]

def generate_case_events(case_number: int) -> List[Dict]:
    """Generate all events for a single case."""
    case_id = generate_case_id()
    events = []
    
    # Generate a random start time within the last 30 days
    current_time = datetime.now()
    case_start_time = current_time - timedelta(days=random.randint(1, 30))
    
    # Calculate target total case duration (around 200 minutes with some variation)
    target_total_duration = random.randint(180, 220)  # 3-3.7 hours
    
    log_info(f"Starting case {case_number + 1}/{NUM_CASES} with ID: {case_id}", "📝", "blue")
    
    # Calculate average time per event pair to achieve target duration
    # We have EVENTS_PER_CASE event pairs, so divide total duration by number of pairs
    avg_time_per_pair = target_total_duration / EVENTS_PER_CASE
    
    for event_number in range(EVENTS_PER_CASE):
        # Add random time between events based on previous event type
        if event_number > 0:
            # Get the end time of the previous event
            prev_event_end = datetime.fromisoformat(events[-1]["timestamp"])
            # Calculate remaining time to distribute
            remaining_pairs = EVENTS_PER_CASE - event_number
            
            # Calculate gap based on remaining time and pairs
            if remaining_pairs > 0:
                gap_minutes = random.uniform(5, 60)
            else:
                gap_minutes = 0
                
            case_start_time = prev_event_end + timedelta(minutes=gap_minutes)
        
        # Create both start and end events
        event_pair = create_event(case_id, event_number, case_start_time)
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
    
    # Log the total case duration
    total_duration = (datetime.fromisoformat(events[-1]["timestamp"]) - 
                     datetime.fromisoformat(events[0]["timestamp"])).total_seconds() / 60
    log_info(
        f"Total case duration: {total_duration:.1f} minutes",
        "⏱️",
        "green"
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

def generate_normally_distributed_duration() -> int:
    """Generate a duration in minutes following a normal distribution.
    
    Returns:
        int: A duration centered around 180 minutes with a standard deviation of 30 minutes.
             The value is clamped to ensure it stays within reasonable bounds (60-300 minutes).
    """
    # Generate a random number from a normal distribution
    # mean = 180, standard deviation = 30
    duration = random.gauss(180, 30)
    
    # Clamp the value to reasonable bounds (60-300 minutes)
    duration = max(60, min(300, duration))
    
    # Convert to integer since we're dealing with minutes
    return int(duration)

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