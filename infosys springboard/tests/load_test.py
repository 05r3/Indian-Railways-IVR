import requests
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

# CONFIGURATION

BASE_URL = "https://indian-railways-ivr1.onrender.com"  
VOICE_URL = f"{BASE_URL}/voice"
CONVERSATION_URL = f"{BASE_URL}/conversation"

NUM_CALLS = 50          
REQUESTS_PER_CALL = 3   # how many interactions in each call
TIMEOUT = 15

headers = {"Content-Type": "application/x-www-form-urlencoded"}

def simulate_single_call(call_num: int):
    """
    Simulates: 
    1. Twilio hitting /voice to start call
    2. User speaking something → /conversation
    3. Follow-up user input → /conversation
    """
    call_id = str(uuid.uuid4())  # Fake CallSid
    results = []

    try:
        # Step 1: Start Call (/voice)
        r1 = requests.post(VOICE_URL, data={"CallSid": call_id}, timeout=TIMEOUT)
        results.append(("voice", r1.status_code))

        # Step 2: First user input (/conversation)
        r2 = requests.post(CONVERSATION_URL, data={
            "CallSid": call_id,
            "SpeechResult": "book ticket"
        }, timeout=TIMEOUT)
        results.append(("conversation_1", r2.status_code))

        # Step 3: Provide follow-up input
        r3 = requests.post(CONVERSATION_URL, data={
            "CallSid": call_id,
            "SpeechResult": "AC"
        }, timeout=TIMEOUT)
        results.append(("conversation_2", r3.status_code))

        return (call_num, True, results)

    except Exception as e:
        return (call_num, False, str(e))


def run_load_test():
    print(f"\n Starting load test: {NUM_CALLS} concurrent IVR calls…\n")

    start = time.time()
    successes = 0
    failures = 0

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(simulate_single_call, i) for i in range(NUM_CALLS)]

        for f in as_completed(futures):
            call_num, ok, result = f.result()
            if ok:
                successes += 1
            else:
                failures += 1
                print(f" Call {call_num} failed → {result}")

    total_time = time.time() - start
    print("\n LOAD TEST RESULTS")
    print("============================")
    print(f"Total Calls Simulated: {NUM_CALLS}")
    print(f"Successful Calls:      {successes}")
    print(f"Failed Calls:          {failures}")
    print(f"Total Time:            {total_time:.2f} sec")
    print(f"Avg Time / Call:       {total_time / NUM_CALLS:.2f} sec")
    print("============================")

# Run test
run_load_test()
