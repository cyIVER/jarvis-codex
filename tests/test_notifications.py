from jarvis_codex.notifications import classify_completion, classify_prompt, get_pack_hints


def test_prompt_classification_phrases():
    assert classify_prompt("make a planning pass")[1] == "Planning pass started."
    assert classify_prompt("review the browser UI")[1] == "Reviewing the interface."
    assert classify_prompt("coordinate the agent swarm")[1] == "Swarm coordination started."
    assert classify_prompt("refresh Worktrunk lanes")[1] == "Worktree operation queued."
    assert classify_prompt("check CUDA acceleration")[1] == "Checking local acceleration."
    assert classify_prompt("inspect GitHub CI")[1] == "Checking the GitHub workflow."
    assert classify_prompt("implement a test fix")[1] == "Code change pass started."
    assert classify_prompt("hello")[1] == "I'm on it."


def test_completion_classification_speaks_only_for_action_needed_by_default():
    assert classify_completion({"success": True, "last-assistant-message": "done"}) == ("success", "", False)
    assert classify_completion({"success": False, "error": "boom"}) == ("error", "The task needs attention.", True)
    assert classify_completion({"success": True, "last-assistant-message": "Approval is needed."}) == (
        "approval-needed",
        "Approval is needed.",
        True,
    )
    assert classify_completion({"success": True, "last-assistant-message": "I am blocked."}) == (
        "blocked",
        "I'm blocked and need input.",
        True,
    )


def test_pack_hints_route_prompt_to_relevant_packs():
    assert get_pack_hints("coordinate an agent harness eval") == ["agent-engineering"]
    assert get_pack_hints("review responsive UI in browser with screenshots") == [
        "design-frontend",
        "browser-testing",
    ]
    assert get_pack_hints("inspect DFIR evidence and write Sentinel KQL") == ["dfir-cyber"]
    assert get_pack_hints("hello") == []
