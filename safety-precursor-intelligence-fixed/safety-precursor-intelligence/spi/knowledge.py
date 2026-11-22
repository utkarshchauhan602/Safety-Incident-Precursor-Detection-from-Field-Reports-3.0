"""Curated, conservative workplace hazard knowledge and response playbooks."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True)
class Playbook:
    key: str
    title: str
    category: str
    terms: tuple[str, ...]
    severity: str
    emergency: bool
    why: str
    immediate_steps: tuple[str, ...]
    prevention: tuple[str, ...]
    follow_up: tuple[str, ...]

PLAYBOOKS: dict[str, Playbook] = {
    "electrical_hazard": Playbook("electrical_hazard", "Electrical equipment or wiring hazard", "Electrical Safety Hazard",
        ("electrical panel", "electrical panels", "faulty panel", "damaged panel", "panel is damaged",
         "panel looks damaged", "problem with the electrical panel", "something wrong with the electrical panel",
         "exposed electrical wire", "exposed wires", "exposed wiring", "damaged electrical cable",
         "damaged cable insulation", "sparking electrical wire", "electrical connection", "loose electrical connection",
         "burning smell from panel", "overheating electrical panel"),
        "High; critical if sparking, smoke, fire or contact occurs", False,
        "Damaged panels, exposed conductors and faulty connections can cause electric shock, burns or fire.",
        ("Keep people away from the panel or damaged wiring; do not touch exposed conductors.",
         "If there is smoke, fire, sparking or immediate danger, raise the site alarm and follow the emergency plan.",
         "Notify the authorized electrical team and supervisor; only qualified personnel should inspect or isolate the equipment.",
         "Do not reset, open, repair or re-energize the equipment until it has been inspected and formally released."),
        ("Arrange inspection by an authorized electrician and review isolation, enclosure integrity and inspection records.",
         "Record the exact location, equipment ID and visible signs without approaching the hazard."),
        ("Is there smoke, sparking, heat or anyone who may have contacted the equipment?",
         "Has the area been kept clear and the authorized electrical team notified?")),
    "electric_shock": Playbook("electric_shock", "Electric shock or electrical contact", "Electrical Safety Hazard",
        ("electric shock", "electrical shock", "got shocked", "worker shocked", "electrocuted", "current passed", "tingling after touching", "electricity hit", "felt current", "electricity passed", "live conductor", "received shock", "got current"),
        "Critical", True, "Electrical contact can cause hidden cardiac, neurological or burn injuries even when the person appears well.",
        ("Raise the site emergency alarm and call the site's emergency medical response immediately.",
         "Do not touch the worker or equipment while an electrical source may still be live.",
         "Keep others away; only authorized electrical responders should isolate energy under the site emergency procedure.",
         "Once the scene is confirmed safe by responders, provide first aid only within your training and follow dispatcher instructions.",
         "Arrange urgent medical assessment even if the worker says they feel normal."),
        ("Investigate the source, isolation, earthing, protective devices and work authorization.",
         "Preserve equipment for an authorized investigation; do not re-energize until formally released.",
         "Review electrical permits, inspection records, training and barriers."),
        ("Is the worker away from the electrical source and is the area confirmed safe by authorized responders?",
         "Has emergency medical help been contacted?", "Where did the contact occur and what equipment was involved?")),
    "fatigue": Playbook("fatigue", "Fatigue, sleeping or reduced alertness on duty", "Human Factors / Fatigue Concern",
        ("sleeping during shift", "worker slept", "sleeping on duty", "fell asleep", "asleep at work", "nodding off", "nodding", "drowsy", "fatigued", "fatigue", "very tired", "dozed off", "dozed", "exhausted", "stay alert", "sleeping while", "asleep while", "sleepy to drive", "too sleepy"),
        "High when safety-critical duties are involved", False, "Reduced alertness can impair reaction time and judgement, especially around vehicles, machinery, heights and hazardous energy.",
        ("If the worker is currently performing a safety-critical task, arrange a safe stop and handover; do not leave equipment in an unsafe state.",
         "Notify the supervisor and follow the site's fitness-for-work and fatigue-management procedure.",
         "Check whether the worker needs a rest period, support or medical assessment; do not shame or diagnose them.",
         "Record observable facts, task, shift duration and time without assumptions about motivation.",
         "Review staffing, workload, overtime, breaks, commute and shift patterns with the appropriate team."),
        ("Review shift scheduling, overtime, rest breaks and consecutive night shifts.",
         "Use a confidential, non-punitive fatigue reporting process.",
         "Assess whether the role is safety-critical and ensure fit-for-duty checks are proportionate."),
        ("Was the worker assigned to a safety-critical task, operating equipment or driving?",
         "Was this during an authorized break in a designated rest area?", "Has this happened repeatedly across shifts?")),
    "unconsciousness": Playbook("unconsciousness", "Unconscious or unresponsive worker", "Medical Emergency",
        ("unconscious", "unresponsive", "passed out", "fainted", "not responding", "collapsed and not waking", "collapsed and did not respond", "collapsed and is not waking", "not waking up"),
        "Critical", True, "An unresponsive person may have a life-threatening medical emergency.",
        ("Call the site's emergency response and local emergency medical services immediately.",
         "Check scene safety before approaching; do not enter a hazardous atmosphere or energized area.",
         "Follow emergency dispatcher instructions and provide first aid or CPR/AED only if trained and safe to do so.",
         "Send someone to guide responders to the exact location."),
        ("Record the timeline and observed facts after emergency care is underway.", "Investigate contributing workplace conditions through the site process."),
        ("Has emergency medical help been called?", "Is the scene safe for trained first responders?")),
    "fire": Playbook("fire", "Fire, smoke or explosion risk", "Fire / Explosion Hazard",
        ("fire", "smoke", "flames", "burning smell", "explosion", "sparks near fuel", "sparks near flammable", "sparks"),
        "Critical", True, "Fire and smoke can spread rapidly and expose workers to burns, toxic smoke and secondary explosions.",
        ("Raise the alarm and follow the site's evacuation and emergency plan.",
         "Move people away using designated routes; do not enter smoke or attempt firefighting unless trained, equipped and authorized.",
         "Call the emergency response team and share the location and materials involved if known.",
         "Do not operate electrical switches or equipment if a flammable atmosphere may be present."),
        ("Review ignition-source controls, hot-work permits, housekeeping and fire protection readiness.", "Keep exits and emergency equipment accessible."),
        ("Has the alarm been raised and are people moving to the designated safe area?", "What location or material is involved, if known safely?")),
    "gas_release": Playbook("gas_release", "Possible gas release", "Chemical / Gas Leak Hazard",
        ("gas leak", "gas alarm", "gas detector", "gas smell", "gas cylinder leak", "hissing cylinder", "hissing sound from gas", "reported gas smell"),
        "Critical", True, "A gas release may be toxic, flammable or displace oxygen; smell is not a reliable safety test.",
        ("Move away, warn others and follow the site's gas-release evacuation procedure.",
         "Avoid switches, vehicles or ignition sources in the suspected area.",
         "Raise the alarm and let trained responders assess the atmosphere with approved instruments.",
         "Do not attempt to locate or stop the leak unless trained and authorized under the emergency plan."),
        ("Maintain detection, alarms, ventilation and cylinder or pipe inspections.", "Review isolation and emergency drill effectiveness."),
        ("Has the area been evacuated according to the site procedure?", "Has the control room or emergency team been notified?")),
    "chemical_spill": Playbook("chemical_spill", "Chemical spill or unknown substance", "Chemical / Gas Leak Hazard",
        ("chemical spill", "chemical leak", "chemical container leaking", "container is leaking", "leaking chemical container", "chemical container leak", "acid leak", "acid spill", "acid is leaking", "chemical is coming out", "solvent leak", "unknown liquid", "chemical smell", "vapour", "vapor", "chlorine"),
        "High / substance dependent", True, "The substance may be corrosive, toxic, flammable or reactive; an unknown spill should be treated cautiously.",
        ("Keep clear and prevent others entering if this can be done safely.", "Do not touch, smell closely or clean an unknown substance.",
         "Notify the control room and trained spill responders; follow the site's spill or evacuation procedure.",
         "Share the label or safety data information only if it can be obtained without exposure."),
        ("Maintain compatible labelled storage, secondary containment and inspected transfer lines.", "Ensure safety data sheets and trained response resources are accessible."),
        ("Is the substance identified from a safe distance or label?", "Has the area been isolated and trained response requested?")),
    "fall_height": Playbook("fall_height", "Fall or working-at-height exposure", "Fall & Working at Heights Hazard",
        ("fell from", "fall from height", "working at height", "scaffold", "scaffolding", "ladder", "harness", "unprotected edge", "floor opening", "floor edge", "guardrail"),
        "High", False, "Falls can cause severe injury; incomplete access equipment and missing edge protection require immediate control.",
        ("Stop the affected work and keep people away from the exposed edge or unsafe access equipment.",
         "Notify the supervisor and competent person responsible for work at height.",
         "Do not use the scaffold or ladder until it has been inspected and released.",
         "If a person has fallen or is injured, activate the site's emergency response; do not move them unless there is immediate danger."),
        ("Verify edge protection, scaffold tags, ladder condition, rescue planning and task permits.", "Use collective fall prevention before relying on personal fall arrest."),
        ("Did anyone fall or sustain an injury?", "Is work still taking place near the exposed edge?")),
    "machine_guard": Playbook("machine_guard", "Machine guarding or hazardous energy", "Mechanical / Procedure Violation",
        ("machine guard", "guard removed", "safety guard", "removed the safety guard", "machine cover is taken off", "interlock bypass", "machine jam", "moving machinery", "moving equipment", "conveyor", "press machine", "emergency stop blocked", "reached into moving machine"),
        "High", False, "Moving parts and defeated guards can cause entanglement, crushing or amputation.",
        ("Keep people clear of the danger zone and stop the task using the approved safe method.",
         "Do not reach into moving equipment or bypass a guard or interlock.",
         "Use the site's lockout/tagout process before inspection or jam clearing; authorized staff must verify zero energy.",
         "Do not restart until guards and safety functions have been checked and released."),
        ("Inspect guards and interlocks, review lockout/tagout and train workers on jam clearing.", "Check whether production pressure contributed to bypassing safeguards."),
        ("Is the machine stopped and isolated under the approved procedure?", "Was a guard or interlock deliberately bypassed?")),
    "slip_trip": Playbook("slip_trip", "Slip, trip or housekeeping condition", "Routine / Non-Hazardous Observation",
        ("slipped", "slip", "tripped", "slippery floor", "slippery floors", "reported slippery floors", "wet floor", "oil on floor", "oil spill", "oil spilled", "oil spilled on factory floor", "floor is slippery", "water pooling", "cable crossing", "loose material", "blocked walkway", "loose cable", "uneven floor"),
        "Medium; higher if injury or hazardous substance", False, "Contaminated floors and blocked walkways can cause falls and may create secondary exposure.",
        ("Warn others and restrict access if safe to do so.", "Arrange cleanup by personnel trained for the material involved.",
         "Do not clean an unknown chemical or oil spill without the correct procedure and equipment.",
         "If anyone was hurt, follow the site's first-aid and incident reporting process."),
        ("Improve spill response, cable management, floor maintenance and routine housekeeping.", "Review recurring locations and shift handover communication."),
        ("Did anyone fall or get injured?", "What was on the floor and has the area been made safe?")),
    "ppe": Playbook("ppe", "Personal protective equipment concern", "Mechanical / Procedure Violation",
        ("helmet missing", "no helmet", "without helmet", "no hard hat", "hard hat missing", "no safety shoes", "without safety shoes", "no gloves", "missing gloves", "missing eye protection", "eye protection", "not wearing ppe", "no harness", "not using required harness"),
        "Medium to High depending on task", False, "Missing or unsuitable PPE can increase exposure but should not replace higher-level engineering controls.",
        ("Pause the task if required protection is absent for the exposure.", "Notify the supervisor and provide suitable, correctly fitted PPE.",
         "Check whether the task assessment and PPE requirements are understood and available."),
        ("Review PPE selection, fit, condition, availability and training.", "Address the hazard at source where feasible rather than relying only on PPE."),
        ("What task and exposure was the worker facing?", "Was the required PPE available and suitable?")),
    "vehicle": Playbook("vehicle", "Vehicle and pedestrian interaction", "Mechanical / Procedure Violation",
        ("forklift", "near miss collision", "vehicle near miss", "reversing vehicle", "reversing truck", "pedestrian route", "vehicle speeding", "crane swing", "crane load swung"),
        "High", False, "Vehicle-pedestrian conflicts can result in crushing injuries, especially at blind corners and loading areas.",
        ("Move to a safe location and keep clear of vehicle routes.", "Report the event to the supervisor and preserve factual details.",
         "Do not approach a moving vehicle to gather information.", "Request a review of traffic separation, visibility, speed and reversing controls."),
        ("Separate pedestrian and vehicle routes, use trained operators and maintain visibility aids.", "Review near misses and traffic management plans."),
        ("Was anyone struck or injured?", "Where did the interaction occur and was the vehicle moving?")),
}

def get_playbook(key: str) -> Playbook | None:
    return PLAYBOOKS.get(key)

def all_playbooks() -> tuple[Playbook, ...]:
    return tuple(PLAYBOOKS.values())

def catalog_terms() -> dict[str, tuple[str, ...]]:
    return {key: value.terms for key, value in PLAYBOOKS.items()}
