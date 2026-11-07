/** English presentation copy for the eight demo cases. IDs and model output stay unchanged. */
export const CASE_COPY_EN: Record<string, { reason: string; factors: string[] }> = {
  "PT-1255": {
    reason: "PT-1255 energy balance suggests a faulty or tampered customer meter, with 96% probability and about 1,753 lei/month in excess loss. Start with remote checks costing 2 lei: re-read customer meters and their event logs. Send a crew only if confirmed.",
    factors: [
      "New meter signals: 0 zero-consumption days, 0 stuck readings, 9 negative readings at night",
      "Estimated normal loss: 195.5 kWh/day, with a P10–P90 interval width of 96.1 kWh",
      "One meter's voltage differs from the transformer pattern: correlation 0.58 versus median 0.90",
      "Transformer meter reads 0.72 times the sum of customer meters",
    ],
  },
  "PT-1293": {
    reason: "Safety risk takes priority regardless of cost. Excess loss is about 52.7 kWh/day, or 5.7% of energy, above P90 on all 14 days, with a 96% score. No suitable crew has capacity tomorrow. Read consumption and events remotely now, prioritise the next plan, and send the dispatcher a request for additional crews.",
    factors: [
      "Excess loss: about 52.7 kWh/day, 5.7% of energy, above P90 on 14 of 14 days",
      "Estimated normal loss: 93.9 kWh/day, with a P10–P90 interval width of 52.2 kWh",
      "One meter's voltage differs from the transformer pattern: correlation 0.56 versus median 0.84",
      "Transformer meter reads 1.15 times the sum of customer meters",
    ],
  },
  "PT-1269": {
    reason: "PT-1269 energy balance suggests technical loss in cables or unbalanced phases, with 100% probability and about 5,019 lei/month in excess loss. A low-voltage grid crew is assigned. Expected value is 15,024 lei. Network inspection costs 486 lei and about 12.2 km of travel costs 75 lei, for a total of 561 lei and net value of 14,463 lei. Crew E-BE-2, stop 2, arrival 11:30.",
    factors: [
      "Excess loss: about 239.0 kWh/day, 17.5% of energy, above P90 on 14 of 14 days",
      "1% of the energy gap occurs at night, 00:00–06:00",
      "One meter's voltage differs from the transformer pattern: correlation 0.70 versus median 0.93",
      "Loss grows with squared load, correlation 0.87, consistent with cable loss",
    ],
  },
  "PT-1017": {
    reason: "The planning model is uncertain: its most likely cause has less than 50% probability. Expected value is 1,357 lei, so the case requires human review. Today's dispatcher queue is full at 25 cases, ordered by risk and value. Monitor this case and reconsider it in the next plan.",
    factors: [
      "Transformer meter reads 1.38 times the sum of customer meters",
      "Neighbouring transformer PT-1044 has about 18.8 kWh/day of surplus, with a 75% match",
      "One meter's voltage differs from the transformer pattern: correlation 0.66 versus median 0.85",
      "3% of the energy gap occurs at night, 00:00–06:00",
    ],
  },
  "PT-1241": {
    reason: "PT-1241 energy balance suggests a misconfigured transformer meter, with 100% probability and about 0 lei/month in excess monetary loss. Start with remote checks costing 2 lei: re-read customer meters and event logs. Send a crew only if confirmed.",
    factors: [
      "Transformer meter reads 2.06 times the sum of customer meters",
      "Excess loss: about 789.9 kWh/day, 97.6% of energy, above P90 on 14 of 14 days",
      "Loss grows with squared load, correlation 0.99, consistent with cable loss",
      "Meter PT-1241-C078 dropped by about 3.2 kWh/day, explaining 0% of the energy gap",
    ],
  },
  "PT-1082": {
    reason: "PT-1082 energy balance suggests technical loss in cables or unbalanced phases, with 100% probability and about 2,985 lei/month in excess loss. A low-voltage grid crew is assigned. Expected value is 8,931 lei. Network inspection costs 486 lei and about 23.3 km of travel costs 117 lei, for a total of 603 lei and net value of 8,328 lei. Crew E-BV-3, stop 2, arrival 12:07.",
    factors: [
      "Excess loss: about 142.1 kWh/day, 25.8% of energy, above P90 on 14 of 14 days",
      "3% of the energy gap occurs at night, 00:00–06:00",
      "One meter's voltage differs from the transformer pattern: correlation 0.67 versus median 0.86",
      "The energy gap rose by about 3.6 kWh/day last week compared with the previous month",
    ],
  },
  "PT-1012": {
    reason: "PT-1012 energy balance suggests technical loss in cables or unbalanced phases, with 100% probability and about 1,886 lei/month in excess loss. A low-voltage grid crew is assigned. Expected value is 5,648 lei. Network inspection costs 486 lei and about 14.1 km of travel costs 82 lei, for a total of 568 lei and net value of 5,080 lei. Crew E-BV-3, stop 1, arrival 09:03.",
    factors: [
      "1% of the energy gap occurs at night, 00:00–06:00",
      "Excess loss: about 89.8 kWh/day, 18.2% of energy, above P90 on 14 of 14 days",
      "Transformer meter reads 1.35 times the sum of customer meters",
      "One meter's voltage differs from the transformer pattern: correlation 0.66 versus median 0.85",
    ],
  },
  "PT-1155": {
    reason: "PT-1155 energy balance suggests technical loss in cables or unbalanced phases, with 100% probability and about 1,455 lei/month in excess loss. A low-voltage grid crew is assigned. Expected value is 4,362 lei. Network inspection costs 486 lei and about 8.0 km of travel costs 53 lei, for a total of 539 lei and net value of 3,824 lei. Crew E-BE-2, stop 1, arrival 08:52.",
    factors: [
      "Excess loss: about 69.3 kWh/day, 21.6% of energy, above P90 on 14 of 14 days",
      "2% of the energy gap occurs at night, 00:00–06:00",
      "Transformer meter reads 1.27 times the sum of customer meters",
      "One meter's voltage differs from the transformer pattern: correlation 0.47 versus median 0.68",
    ],
  },
}

export const EVALUATION_NAMES_EN: Record<string, string> = {
  agent: "Agent with rules and OR-Tools",
  top_k_scor: "Top-K by score",
  primul_venit: "First come, first served",
  aleator: "Random",
  doar_contoare: "Meters only",
}
