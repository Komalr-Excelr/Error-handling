import time
from src.call_agent import CallAgent, load_config


def main():
    cfg = load_config()
    # Faster breaker reset for demo
    cfg["circuit_breaker"]["reset_timeout_seconds"] = 1

    agent = CallAgent(cfg)

    # Prepare contacts
    agent.crm.contacts = [
        {"id": 1, "name": "Alice", "phone": "+1000001"},
        {"id": 2, "name": "Bob", "phone": "+1000002"},
        {"id": 3, "name": "Cara", "phone": "+1000003"},
    ]

    # Simulate required scenario: ElevenLabs returns 503 and is unhealthy
    agent.eleven.set_healthy(False)
    agent.eleven.simulate_503_once()

    # Visualize retry backoff without waiting
    agent.eleven_retry.sleep = lambda s: print(f"[Retry] backoff sleeping {s}s (simulated)")
    # Visualize alerts without sending
    agent.alerts.alert_critical = lambda subject, message: print(f"[Alert] {subject}: {message}")

    print("[Scenario] Starting processing with ElevenLabs unhealthy (expect retries and failure)")
    agent.process_queue()
    print(f"[Scenario] Circuit breaker state after failures: {agent.eleven_cb.state()}")

    # Recover service
    agent.eleven.set_healthy(True)
    agent.health.run_once()
    print(f"[Scenario] Circuit breaker state after health check: {agent.eleven_cb.state()}")

    # Add more contacts to demonstrate resumed processing
    agent.crm.contacts = [
        {"id": 4, "name": "Dora", "phone": "+1000004"},
        {"id": 5, "name": "Evan", "phone": "+1000005"},
    ]

    print("[Scenario] Resuming processing with ElevenLabs healthy (expect success)")
    agent.process_queue()


if __name__ == "__main__":
    main()
