from spi.triage import detect_hazard

def test_electrical_panel_problem_is_recognized():
    match = detect_hazard("I am not sure, but I think something is wrong with the electrical panel. Can you help me?")
    assert match is not None
    assert match.key == "electrical_hazard"

def test_repeated_slippery_floor_report_is_recognized():
    match = detect_hazard("Several workers have reported slippery floors in the same area this week.")
    assert match is not None
    assert match.key == "slip_trip"

def test_chemical_container_leak_is_recognized():
    match = detect_hazard("I found a chemical container leaking near the storage area. How should I report it?")
    assert match is not None
    assert match.key == "chemical_spill"
