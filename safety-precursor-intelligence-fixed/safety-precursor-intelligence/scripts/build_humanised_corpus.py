"""Build the deterministic 50,000-row synthetic HSE conversation corpus.

The corpus is for QA, phrasing coverage and local conversational retrieval. It is
not a real incident dataset and must not be described as model validation.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "spi" / "data" / "humanised_hse_conversations.jsonl"

HAZARDS = {
    "electric_shock": {
        "phrases": ["a worker received an electric shock", "someone felt an electrical current", "a colleague was shocked by equipment", "there is exposed live wiring", "a person reported tingling after touching metalwork", "an electrical cable has damaged insulation", "a panel has accessible live parts", "a worker made contact with an energized part", "sparking was seen at an electrical connection", "a person may have suffered electrical contact"],
        "question": "Is everyone away from the source, and have emergency responders been contacted?",
        "acks": ["Thank you for telling me; electrical contact needs to be treated seriously.", "I'm glad you raised this. Let's put people's immediate safety first.", "That sounds concerning. I'll help you capture the facts without delaying the site response.", "Thanks for speaking up. Even a brief electrical contact can need urgent assessment.", "I hear you. Let's first make sure nobody is exposed to the electrical source."],
    },
    "unconsciousness": {
        "phrases": ["a worker is unconscious", "someone collapsed and is not responding", "a colleague has passed out", "a person fainted and has not woken", "a worker is unresponsive", "someone collapsed near the work area", "a person is not waking up", "a colleague is not responding when spoken to", "a worker has become suddenly unresponsive", "someone may need urgent medical help"],
        "question": "Has the site emergency response and emergency medical help been called?",
        "acks": ["Thank you for alerting me. An unresponsive person needs immediate emergency help.", "I'm sorry this is happening. Please put the emergency response ahead of documenting details.", "I hear the concern. Let's focus on getting trained help to the person now.", "Thanks for reporting this. Do not wait for this chat before activating the emergency plan.", "That may be serious. Please make sure the emergency team has been contacted."],
    },
    "fire": {
        "phrases": ["smoke is coming from equipment", "there are flames near the work area", "a burning smell is coming from a machine", "sparks appeared near flammable material", "a small fire was seen at the site", "an alarm indicates a possible fire", "a hot surface appears to be smouldering", "there may have been an explosion", "smoke was noticed in the storage area", "a fire risk was reported near operations"],
        "question": "Has the alarm been raised and are people following the site's evacuation procedure?",
        "acks": ["Thanks for raising this. Fire and smoke reports should be acted on immediately.", "I understand. Let's prioritize the alarm and safe evacuation process.", "That could escalate quickly. Please follow the site's emergency plan first.", "Thank you for reporting it. Keep people away from the affected area.", "I'm glad you spoke up. The emergency team needs to know about this promptly."],
    },
    "gas_release": {
        "phrases": ["there may be a gas leak", "a gas detector alarm has activated", "a hissing sound is coming from a cylinder", "someone noticed a gas smell", "vapour may be escaping from a line", "a gas connection appears to be leaking", "an alarm sounded near the manifold", "a suspected gas release was reported", "a cylinder valve may not be sealed", "workers reported an unusual gas odour"],
        "question": "Has the area been cleared under the site procedure and has the emergency team been notified?",
        "acks": ["Thank you for reporting this. A suspected gas release should be treated cautiously.", "I hear you. Please move away and follow the site's gas emergency procedure.", "That is important to raise. Trained responders should assess the area.", "Thanks for speaking up. Smell alone cannot confirm whether an area is safe.", "Let's put distance between people and the suspected release first."],
    },
    "chemical_spill": {
        "phrases": ["a chemical container is leaking", "there is an unknown liquid on the floor", "acid has spilled near the process line", "solvent is escaping from a pump connection", "a chemical smell was noticed in storage", "a transfer hose appears to be leaking", "vapour is visible near a chemical drum", "a container label is missing near a spill", "a chemical line has a wet patch", "a substance was found leaking in the work area"],
        "question": "Has the area been kept clear and have trained spill responders been notified?",
        "acks": ["Thanks for reporting this. Please don't touch or attempt to clean an unknown substance.", "I understand. Let's keep people clear while the trained response team is contacted.", "That is worth reporting. The substance should only be assessed using the site procedure.", "Thank you for speaking up. Avoid close contact with the spill or its vapour.", "I hear your concern. Let's capture what is known without exposing anyone."],
    },
    "fall_height": {
        "phrases": ["a scaffold platform has a loose board", "a ladder is damaged", "an open edge has no guardrail", "a worker is near an unprotected floor opening", "a harness is not connected", "a scaffold inspection tag is missing", "an access ladder moves under load", "materials are stored beside an open edge", "a worker may fall from an elevated platform", "toe boards are missing from a work platform"],
        "question": "Has the affected work stopped and is everyone clear of the fall exposure?",
        "acks": ["Thanks for flagging this. Work-at-height concerns deserve prompt attention.", "I understand. Let's keep people away from the exposed edge or access equipment.", "That could lead to a serious fall. Please involve the competent site person.", "Thank you for reporting it. The equipment should not be used until checked and released.", "I'm glad you raised this. Let's make sure the area is controlled first."],
    },
    "machine_guard": {
        "phrases": ["a machine guard has been removed", "an interlock was bypassed", "someone reached into moving equipment", "a conveyor is running with an open guard", "a machine jam is being cleared while running", "the emergency stop is blocked", "equipment was restarted before isolation", "a press is operating without its guard", "lockout tagout was not applied", "a worker entered a machine danger zone"],
        "question": "Is the equipment stopped and isolated under the approved site procedure?",
        "acks": ["Thanks for telling me. Moving machinery and bypassed safeguards can cause severe harm.", "I hear you. Let's keep everyone out of the danger zone first.", "That is important to address. No one should reach into moving equipment.", "Thank you for speaking up. The approved isolation process must come before maintenance.", "Let's focus on controlling access and involving the authorized supervisor."],
    },
    "slip_trip": {
        "phrases": ["oil has spilled on the walkway", "the floor is wet near the entrance", "a cable crosses the pedestrian route", "materials are blocking an access path", "someone slipped on a wet floor", "the floor surface is uneven", "water is pooling near the work area", "loose material is scattered on the floor", "a walkway is obstructed", "a trip hazard was noticed near the stairs"],
        "question": "Has access been controlled and has the condition been reported for safe cleanup or repair?",
        "acks": ["Thanks for noticing and reporting this. Small floor hazards can still cause injuries.", "I understand. Let's prevent others from entering the affected area.", "Good catch. The cleanup or repair should follow the site's safe procedure.", "Thank you for speaking up. Can we capture the exact location and current controls?", "That is useful information. Recurring locations should be tracked, not just cleaned once."],
    },
    "ppe": {
        "phrases": ["a worker is missing a required helmet", "someone is not wearing eye protection", "gloves are missing for the task", "safety shoes are not being worn", "a harness is unavailable for the job", "the supplied PPE does not fit", "a face shield is damaged", "the required hearing protection is not being used", "a worker has unsuitable protective equipment", "PPE stock is not available at the work area"],
        "question": "What task and exposure were involved, and was suitable PPE available?",
        "acks": ["Thanks for raising this. Let's understand the task and the protection it requires.", "I hear you. PPE needs to be suitable, available and correctly fitted.", "That is worth checking. The underlying hazard should also be controlled where possible.", "Thank you for reporting it without blame. Let's capture what was observed.", "I understand. Let's find out whether the equipment was missing, unsuitable or damaged."],
    },
    "vehicle": {
        "phrases": ["a forklift nearly hit a pedestrian", "a reversing truck came close to a worker", "a vehicle was travelling too fast", "a pedestrian entered a vehicle route", "a crane load swung near workers", "a vehicle blind spot caused a near miss", "a reversing alarm was not working", "a mobile plant route crossed a walkway", "a vehicle and pedestrian came into conflict", "a load moved unexpectedly near a work team"],
        "question": "Was anyone struck or injured, and where did the vehicle interaction happen?",
        "acks": ["Thanks for reporting the near miss. Vehicle interactions can have serious consequences.", "I understand. Let's keep people clear of the vehicle route while it is reviewed.", "That is important to capture, even though nobody may have been injured.", "Thank you for speaking up. The location and traffic controls will help the review.", "I hear you. Let's record the facts without assuming who was at fault."],
    },
}

AREAS = ["loading bay", "north access gate", "maintenance workshop", "production line", "chemical store", "utility room", "warehouse aisle", "tank farm", "dispatch area", "contractor work zone"]
TIMES = ["morning shift", "afternoon shift", "night shift", "shift handover", "routine maintenance", "equipment cleaning", "contractor activity", "pre-start inspection", "material transfer", "shutdown preparation"]
FRAMES = [
    "I noticed {phrase} near the {area} during {time}.",
    "A colleague reported that {phrase} at the {area} during {time}.",
    "Can you help me understand what to do? {phrase_cap} was observed in the {area} during {time}.",
    "I want to log a safety observation: {phrase} at the {area} during {time}.",
    "This may be a precursor worth tracking: {phrase} in the {area} during {time}.",
]

def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with OUT.open("w", encoding="utf-8", newline="\n") as handle:
        for hazard_key, data in HAZARDS.items():
            for phrase in data["phrases"]:
                for frame in FRAMES:
                    for area in AREAS:
                        for time in TIMES:
                            user_text = frame.format(phrase=phrase, phrase_cap=phrase[0].upper()+phrase[1:], area=area, time=time)
                            ack_index = (len(user_text) + len(area) + len(time)) % len(data["acks"])
                            record = {
                                "id": f"HSE-{count+1:05d}",
                                "hazard_key": hazard_key,
                                "intent": "safety_observation",
                                "user_text": user_text,
                                "humanised_acknowledgement": data["acks"][ack_index],
                                "clarifying_question": data["question"],
                                "synthetic": True,
                                "dataset_version": "3.0",
                            }
                            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                            count += 1
    if count != 50_000:
        raise SystemExit(f"Expected 50000 rows, wrote {count}")
    print(f"Wrote {count:,} conversation examples to {OUT}")

if __name__ == "__main__":
    main()
