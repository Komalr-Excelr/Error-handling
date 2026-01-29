from src.call_agent import CallAgent, load_config
from src.exceptions.errors import ServiceUnavailableError


def test_required_scenario_elevenlabs_503(monkeypatch):
    cfg = load_config()
    # Reduce reset timeout for faster test
    cfg["circuit_breaker"]["reset_timeout_seconds"] = 1
    agent = CallAgent(cfg)

    # Make CRM have two contacts
    agent.crm.contacts = [
        {"id": 1, "name": "Alice", "phone": "+1000001"},
        {"id": 2, "name": "Bob", "phone": "+1000002"},
    ]

    # Simulate 503 on first call and then keep unhealthy until health check recovers
    agent.eleven.set_healthy(False)
    agent.eleven.simulate_503_once()

    # Stub alert handler to capture alerts instead of sending
    sent_alerts = {"messages": []}

    def fake_alert(subject, message):
        sent_alerts["messages"].append((subject, message))

    monkeypatch.setattr(agent.alerts, "alert_critical", fake_alert)

    # Stub sleep in retry handler to avoid delays
    agent.eleven_retry.sleep = lambda s: None

    # Run processing: it should attempt first contact, exhaust retries, mark failed, alert, then continue
    agent.process_queue()

    # Circuit breaker should be open for ElevenLabs
    assert agent.eleven_cb.state() in (agent.eleven_cb.OPEN, agent.eleven_cb.HALF_OPEN)
    assert len(sent_alerts["messages"]) >= 1

    # Now set service healthy and run health checks manually to reset
    agent.eleven.set_healthy(True)
    # Run a single health check cycle
    agent.health.run_once()
    assert agent.eleven_cb.state() == agent.eleven_cb.CLOSED
