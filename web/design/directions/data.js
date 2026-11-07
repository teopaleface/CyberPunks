// Date comune pentru machete (din contracts/fixtures, sintetice).
window.TURA = {
 "_note": "Date reale din contracts/fixtures (exemple ilustrative, SINTETICE) + config/area.yaml + config/crews.yaml. Generat pentru machetele de direcție vizuală.",
 "plan": {
  "contract_version": "1.0",
  "plan_id": "PLAN-fixture",
  "plan_date": "2026-11-09",
  "generated_at": "2026-11-08T06:00:00+02:00",
  "planner_version": "planner@fixture",
  "scenario": "fixture",
  "summary": {
   "items_in": 8,
   "items_valid": 7,
   "items_invalid": 1,
   "assigned": 3,
   "deferred": 1,
   "human_review": 1,
   "remote_actions": 0,
   "notifications": 1,
   "crews_used": 2,
   "expected_value_lei": 2741.2,
   "total_km": 31.4
  },
  "routes": [
   {
    "crew_id": "E-BV-2",
    "depot_id": "D-BUC-V",
    "stops": [
     {
      "seq": 1,
      "work_item_id": "A-20261109-MTR-004217",
      "eta": "2026-11-09T08:25:00+02:00",
      "duration_min": 40,
      "travel_km": 6.1
     },
     {
      "seq": 2,
      "work_item_id": "A-20261109-MTR-019833",
      "eta": "2026-11-09T09:50:00+02:00",
      "duration_min": 40,
      "travel_km": 11.8
     }
    ],
    "total_km": 29.0,
    "total_work_min": 80,
    "total_travel_min": 95
   },
   {
    "crew_id": "E-BV-3",
    "depot_id": "D-BUC-V",
    "stops": [
     {
      "seq": 1,
      "work_item_id": "C-20261109-PT-1432",
      "eta": "2026-11-09T11:00:00+02:00",
      "duration_min": 120,
      "travel_km": 2.4
     }
    ],
    "total_km": 4.8,
    "total_work_min": 120,
    "total_travel_min": 14
   }
  ],
  "decisions": [
   {
    "work_item_id": "A-20261109-MTR-004217",
    "decision": "assigned",
    "reason_ro": "Valoarea așteptată depășește costul vizitei și există capacitate.",
    "rule_id": "R-VALUE-OVER-COST",
    "threshold": {
     "min_net_value_lei": 0.0,
     "score_min": 0.5
    },
    "priority_score": 1239.75,
    "rank": 1,
    "crew_id": "E-BV-2",
    "audit_id": "e8d43cf9-6bf3-4b30-8e5e-dd4a7cb6eb3f"
   },
   {
    "work_item_id": "C-20261109-PT-1432",
    "decision": "assigned",
    "reason_ro": "Valoarea așteptată depășește costul vizitei și există capacitate.",
    "rule_id": "R-VALUE-OVER-COST",
    "threshold": {
     "min_net_value_lei": 0.0,
     "score_min": 0.5
    },
    "priority_score": 746.2,
    "rank": 2,
    "crew_id": "E-BV-3",
    "audit_id": "2c90a4cf-0626-4bae-a6ae-0ad3121b8e44"
   },
   {
    "work_item_id": "A-20261109-MTR-019833",
    "decision": "assigned",
    "reason_ro": "Valoarea așteptată depășește costul vizitei și există capacitate.",
    "rule_id": "R-VALUE-OVER-COST",
    "threshold": {
     "min_net_value_lei": 0.0,
     "score_min": 0.5
    },
    "priority_score": 912.0,
    "rank": 3,
    "crew_id": "E-BV-2",
    "audit_id": "73600e48-4c2a-4ab6-bc8c-2eb0e283083a"
   },
   {
    "work_item_id": "A-20261109-MTR-027710",
    "decision": "human_review",
    "reason_ro": "Modelul nu e sigur: prea puțin istoric. Decide un om.",
    "rule_id": "R-ABSTAIN",
    "threshold": {},
    "priority_score": null,
    "rank": null,
    "crew_id": null,
    "audit_id": "4285add9-20f9-4885-89d6-00d945b024e8"
   }
  ],
  "alerts": [
   {
    "alert_id": "AL-1",
    "severity": "warning",
    "title_ro": "Risc de avarii în zona Medgidia",
    "body_ro": "Rafale de 85 km/h între 12:00 și 20:00. Recomand o echipă în zonă de la 11:00.",
    "work_item_ids": [
     "B-20261109-CT-MEDGIDIA"
    ],
    "channel": "dispecerat",
    "created_at": "2026-11-08T06:00:00+02:00"
   }
  ],
  "notifications": [
   {
    "notification_id": "N-1",
    "audience": "prosumatori",
    "asset_id": "PT-1432",
    "message_ro": "Mâine între 11 și 15 e soare puternic. Dacă puteți, porniți atunci mașina de spălat și boilerul.",
    "scheduled_for": "2026-11-08T18:00:00+02:00",
    "work_item_id": "C-20261109-PT-1432",
    "demo_only": true
   }
  ],
  "sources_status": {
   "A": "ok",
   "B": "ok",
   "C": "ok"
  }
 },
 "work_items": [
  {
   "work_item_id": "A-20261109-MTR-004217",
   "source": "A",
   "kind": "meter_inspection",
   "asset_id": "MTR-004217",
   "asset_type": "meter",
   "location": {
    "lat": 44.4321,
    "lon": 26.0254,
    "zone_id": "B-S6",
    "county": "București",
    "label": "Contor MTR-004217"
   },
   "target_date": "2026-11-09",
   "prediction": {
    "model_id": "a-lgbm",
    "model_version": "a-lgbm@fixture",
    "prediction_id": "69136ff3-7a5a-454f-a9a6-727700efb5ea",
    "label": "tamper",
    "score": 0.87,
    "interval_low": 0.69,
    "interval_high": 0.95,
    "confidence": "high",
    "abstain": false,
    "abstain_reason": null
   },
   "impact": {
    "expected_value_lei": 1239.75,
    "value_if_true_lei": 1425.0,
    "customers_affected": 1,
    "urgency_hours": 72,
    "safety_flag": true,
    "assumptions_ref": "meters"
   },
   "effort": {
    "duration_min": 40,
    "crew_skill": "metering",
    "crew_size": 2,
    "requires_planned_outage": false
   },
   "explanation": {
    "top_factors": [
     {
      "feature": "zero_run_days_30d",
      "label_ro": "9 zile la rând cu consum zero",
      "value": 9,
      "contribution": 0.31
     },
     {
      "feature": "peer_ratio_post",
      "label_ro": "cu 72% sub vecinii de pe același post",
      "value": 0.28,
      "contribution": 0.22
     }
    ],
    "similar_cases": [
     {
      "case_id": "SGCC-0193",
      "outcome": "furt_confirmat",
      "similarity": 0.91
     }
    ],
    "summary_ro": "Consum zero 9 zile după un istoric stabil și mult sub vecini. Merită verificat la fața locului."
   },
   "data_quality": {
    "missing_ratio": 0.04,
    "input_issues": [],
    "synthetic": true,
    "data_sources": [
     "fixture ilustrativ"
    ]
   },
   "recommended_action": "inspect_on_site",
   "created_at": "2026-11-08T06:00:00+02:00",
   "extra": {
    "series_ref": "outputs/series/A/MTR-004217.json"
   }
  },
  {
   "work_item_id": "A-20261109-MTR-019833",
   "source": "A",
   "kind": "meter_inspection",
   "asset_id": "MTR-019833",
   "asset_type": "meter",
   "location": {
    "lat": 44.4512,
    "lon": 26.1287,
    "zone_id": "B-S2",
    "county": "București",
    "label": "Contor MTR-019833"
   },
   "target_date": "2026-11-09",
   "prediction": {
    "model_id": "a-lgbm",
    "model_version": "a-lgbm@fixture",
    "prediction_id": "9a3fd03f-3fc6-43ad-a041-ca5fcb97e7e8",
    "label": "faulty",
    "score": 0.64,
    "interval_low": 0.46,
    "interval_high": 0.72,
    "confidence": "medium",
    "abstain": false,
    "abstain_reason": null
   },
   "impact": {
    "expected_value_lei": 912.0,
    "value_if_true_lei": 1425.0,
    "customers_affected": 1,
    "urgency_hours": 72,
    "safety_flag": false,
    "assumptions_ref": "meters"
   },
   "effort": {
    "duration_min": 40,
    "crew_skill": "metering",
    "crew_size": 2,
    "requires_planned_outage": false
   },
   "explanation": {
    "top_factors": [
     {
      "feature": "zero_run_days_30d",
      "label_ro": "9 zile la rând cu consum zero",
      "value": 9,
      "contribution": 0.31
     },
     {
      "feature": "peer_ratio_post",
      "label_ro": "cu 72% sub vecinii de pe același post",
      "value": 0.28,
      "contribution": 0.22
     }
    ],
    "similar_cases": [
     {
      "case_id": "SGCC-0193",
      "outcome": "furt_confirmat",
      "similarity": 0.91
     }
    ],
    "summary_ro": "Consum zero 9 zile după un istoric stabil și mult sub vecini. Merită verificat la fața locului."
   },
   "data_quality": {
    "missing_ratio": 0.04,
    "input_issues": [],
    "synthetic": true,
    "data_sources": [
     "fixture ilustrativ"
    ]
   },
   "recommended_action": "inspect_on_site",
   "created_at": "2026-11-08T06:00:00+02:00",
   "extra": {
    "series_ref": "outputs/series/A/MTR-019833.json"
   }
  },
  {
   "work_item_id": "A-20261109-MTR-027710",
   "source": "A",
   "kind": "meter_inspection",
   "asset_id": "MTR-027710",
   "asset_type": "meter",
   "location": {
    "lat": 44.408,
    "lon": 26.0901,
    "zone_id": "B-S5",
    "county": "București",
    "label": "Contor MTR-027710"
   },
   "target_date": "2026-11-09",
   "prediction": {
    "model_id": "a-lgbm",
    "model_version": "a-lgbm@fixture",
    "prediction_id": "dad45200-729e-46c0-ab05-6bc29eea9ef3",
    "label": "faulty",
    "score": 0.52,
    "interval_low": 0.34,
    "interval_high": 0.6,
    "confidence": "low",
    "abstain": true,
    "abstain_reason": "doar 11 zile de istoric după montare"
   },
   "impact": {
    "expected_value_lei": 741.0,
    "value_if_true_lei": 1425.0,
    "customers_affected": 1,
    "urgency_hours": 72,
    "safety_flag": false,
    "assumptions_ref": "meters"
   },
   "effort": {
    "duration_min": 40,
    "crew_skill": "metering",
    "crew_size": 2,
    "requires_planned_outage": false
   },
   "explanation": {
    "top_factors": [
     {
      "feature": "zero_run_days_30d",
      "label_ro": "9 zile la rând cu consum zero",
      "value": 9,
      "contribution": 0.31
     },
     {
      "feature": "peer_ratio_post",
      "label_ro": "cu 72% sub vecinii de pe același post",
      "value": 0.28,
      "contribution": 0.22
     }
    ],
    "similar_cases": [
     {
      "case_id": "SGCC-0193",
      "outcome": "furt_confirmat",
      "similarity": 0.91
     }
    ],
    "summary_ro": "Consum zero 9 zile după un istoric stabil și mult sub vecini. Merită verificat la fața locului."
   },
   "data_quality": {
    "missing_ratio": 0.04,
    "input_issues": [],
    "synthetic": true,
    "data_sources": [
     "fixture ilustrativ"
    ]
   },
   "recommended_action": "human_review",
   "created_at": "2026-11-08T06:00:00+02:00",
   "extra": {
    "series_ref": "outputs/series/A/MTR-027710.json"
   }
  },
  {
   "work_item_id": "B-20261109-CT-MEDGIDIA",
   "source": "B",
   "kind": "storm_prepositioning",
   "asset_id": "CT-MEDGIDIA",
   "asset_type": "zone",
   "location": {
    "lat": 44.25,
    "lon": 28.2731,
    "zone_id": "CT-MEDGIDIA",
    "county": "Constanța",
    "label": "Zona CT-MEDGIDIA"
   },
   "target_date": "2026-11-09",
   "time_window": {
    "start": "2026-11-09T12:00:00+02:00",
    "end": "2026-11-09T20:00:00+02:00"
   },
   "prediction": {
    "model_id": "b-lgbm-quantile",
    "model_version": "b-lgbm@fixture",
    "prediction_id": "dd7531fd-1bb3-45a8-b1c6-102a7b9a97b8",
    "label": "outage_risk",
    "score": 0.78,
    "interval_low": 0.5800000000000001,
    "interval_high": 0.88,
    "point_estimate": 1260.0,
    "point_unit": "clienți fără curent (vârf)",
    "point_interval": [
     210.0,
     3150.0
    ],
    "confidence": "medium"
   },
   "impact": {
    "expected_value_lei": 29484.0,
    "value_if_true_lei": 37800.0,
    "customers_affected": 1260,
    "urgency_hours": 6,
    "safety_flag": false,
    "assumptions_ref": "storm"
   },
   "effort": {
    "duration_min": 480,
    "crew_skill": "mv_grid",
    "crew_size": 3,
    "requires_planned_outage": false
   },
   "explanation": {
    "top_factors": [
     {
      "feature": "wind_gust_max_kmh",
      "label_ro": "rafale de vânt de 85 km/h",
      "value": 85,
      "contribution": 0.41
     },
     {
      "feature": "precip_48h_mm",
      "label_ro": "32 mm de ploaie în 48 de ore",
      "value": 32,
      "contribution": 0.12
     }
    ],
    "similar_cases": [
     {
      "case_id": "EAGLEI-2019-06-OH-123",
      "outcome": "avarii_extinse",
      "similarity": 0.84
     }
    ],
    "summary_ro": "Rafale de 85 km/h după-amiaza. În situații asemănătoare au căzut linii în mai multe localități."
   },
   "data_quality": {
    "missing_ratio": 0.0,
    "input_issues": [],
    "synthetic": false,
    "data_sources": [
     "fixture ilustrativ"
    ]
   },
   "recommended_action": "preposition_crew",
   "created_at": "2026-11-08T06:00:00+02:00"
  },
  {
   "work_item_id": "B-20261109-IF-SNAGOV",
   "source": "B",
   "kind": "storm_prepositioning",
   "asset_id": "IF-SNAGOV",
   "asset_type": "zone",
   "location": {
    "lat": 44.704,
    "lon": 26.172,
    "zone_id": "IF-SNAGOV",
    "county": "Ilfov",
    "label": "Zona IF-SNAGOV"
   },
   "target_date": "2026-11-09",
   "time_window": {
    "start": "2026-11-09T12:00:00+02:00",
    "end": "2026-11-09T20:00:00+02:00"
   },
   "prediction": {
    "model_id": "b-lgbm-quantile",
    "model_version": "b-lgbm@fixture",
    "prediction_id": "d7b945c5-5532-4ff5-adc3-5132c38b86d8",
    "label": "outage_risk",
    "score": 0.41,
    "interval_low": 0.20999999999999996,
    "interval_high": 0.51,
    "point_estimate": 540.0,
    "point_unit": "clienți fără curent (vârf)",
    "point_interval": [
     90.0,
     1350.0
    ],
    "confidence": "medium"
   },
   "impact": {
    "expected_value_lei": 6642.0,
    "value_if_true_lei": 16200.0,
    "customers_affected": 540,
    "urgency_hours": 6,
    "safety_flag": false,
    "assumptions_ref": "storm"
   },
   "effort": {
    "duration_min": 480,
    "crew_skill": "mv_grid",
    "crew_size": 3,
    "requires_planned_outage": false
   },
   "explanation": {
    "top_factors": [
     {
      "feature": "wind_gust_max_kmh",
      "label_ro": "rafale de vânt de 85 km/h",
      "value": 85,
      "contribution": 0.41
     },
     {
      "feature": "precip_48h_mm",
      "label_ro": "32 mm de ploaie în 48 de ore",
      "value": 32,
      "contribution": 0.12
     }
    ],
    "similar_cases": [
     {
      "case_id": "EAGLEI-2019-06-OH-123",
      "outcome": "avarii_extinse",
      "similarity": 0.84
     }
    ],
    "summary_ro": "Rafale de 85 km/h după-amiaza. În situații asemănătoare au căzut linii în mai multe localități."
   },
   "data_quality": {
    "missing_ratio": 0.0,
    "input_issues": [],
    "synthetic": false,
    "data_sources": [
     "fixture ilustrativ"
    ]
   },
   "recommended_action": "preposition_crew",
   "created_at": "2026-11-08T06:00:00+02:00"
  },
  {
   "work_item_id": "C-20261109-PT-1432",
   "source": "C",
   "kind": "voltage_mitigation",
   "asset_id": "PT-1432",
   "asset_type": "transformer_post",
   "location": {
    "lat": 44.4285,
    "lon": 25.9905,
    "zone_id": "IF-CHIAJNA",
    "county": "Ilfov",
    "label": "PT-1432, IF-CHIAJNA"
   },
   "target_date": "2026-11-09",
   "time_window": {
    "start": "2026-11-09T11:00:00+02:00",
    "end": "2026-11-09T15:00:00+02:00"
   },
   "prediction": {
    "model_id": "c-surrogate",
    "model_version": "c-lgbm@fixture",
    "prediction_id": "890a27e2-c5c0-452b-bda8-a79bd50db55c",
    "label": "overvoltage",
    "score": 0.91,
    "point_estimate": 1.12,
    "point_unit": "tensiune maximă (pu)",
    "point_interval": [
     1.1,
     1.135
    ],
    "confidence": "high"
   },
   "impact": {
    "expected_value_lei": 746.2,
    "value_if_true_lei": 820.0,
    "customers_affected": 38,
    "urgency_hours": 30,
    "safety_flag": false,
    "assumptions_ref": "voltage"
   },
   "effort": {
    "duration_min": 120,
    "crew_skill": "lv_grid",
    "crew_size": 3,
    "requires_planned_outage": true
   },
   "explanation": {
    "top_factors": [
     {
      "feature": "pv_kw_per_kva",
      "label_ro": "410 kW de panouri pe un transformator de 250 kVA",
      "value": 1.64,
      "contribution": 0.38
     },
     {
      "feature": "irradiance_noon_wm2",
      "label_ro": "soare puternic la prânz, 890 W/m²",
      "value": 890,
      "contribution": 0.27
     }
    ],
    "similar_cases": [],
    "summary_ro": "Mâine la prânz tensiunea poate urca la 1,12 față de limita de 1,10. Invertoarele s-ar opri singure."
   },
   "data_quality": {
    "missing_ratio": 0.0,
    "input_issues": [],
    "synthetic": true,
    "data_sources": [
     "fixture ilustrativ"
    ]
   },
   "recommended_action": "adjust_tap",
   "created_at": "2026-11-08T06:00:00+02:00"
  },
  {
   "work_item_id": "C-20261109-PT-0877",
   "source": "C",
   "kind": "voltage_mitigation",
   "asset_id": "PT-0877",
   "asset_type": "transformer_post",
   "location": {
    "lat": 44.559,
    "lon": 26.061,
    "zone_id": "IF-OTOPENI",
    "county": "Ilfov",
    "label": "PT-0877, IF-OTOPENI"
   },
   "target_date": "2026-11-09",
   "time_window": {
    "start": "2026-11-09T11:00:00+02:00",
    "end": "2026-11-09T15:00:00+02:00"
   },
   "prediction": {
    "model_id": "c-surrogate",
    "model_version": "c-lgbm@fixture",
    "prediction_id": "8765cd0b-18b7-481c-8479-3054b0a1c47e",
    "label": "overvoltage",
    "score": 0.58,
    "point_estimate": 1.095,
    "point_unit": "tensiune maximă (pu)",
    "point_interval": [
     1.075,
     1.11
    ],
    "confidence": "medium"
   },
   "impact": {
    "expected_value_lei": 475.6,
    "value_if_true_lei": 820.0,
    "customers_affected": 38,
    "urgency_hours": 30,
    "safety_flag": false,
    "assumptions_ref": "voltage"
   },
   "effort": {
    "duration_min": 120,
    "crew_skill": "lv_grid",
    "crew_size": 3,
    "requires_planned_outage": true
   },
   "explanation": {
    "top_factors": [
     {
      "feature": "pv_kw_per_kva",
      "label_ro": "410 kW de panouri pe un transformator de 250 kVA",
      "value": 1.64,
      "contribution": 0.38
     },
     {
      "feature": "irradiance_noon_wm2",
      "label_ro": "soare puternic la prânz, 890 W/m²",
      "value": 890,
      "contribution": 0.27
     }
    ],
    "similar_cases": [],
    "summary_ro": "Mâine la prânz tensiunea poate urca la 1,12 față de limita de 1,10. Invertoarele s-ar opri singure."
   },
   "data_quality": {
    "missing_ratio": 0.0,
    "input_issues": [],
    "synthetic": true,
    "data_sources": [
     "fixture ilustrativ"
    ]
   },
   "recommended_action": "adjust_tap",
   "created_at": "2026-11-08T06:00:00+02:00"
  }
 ],
 "invalid_items": [
  {
   "work_item_id": "A-20261109-MTR-BAD",
   "source": "A",
   "kind": "meter_inspection",
   "asset_id": "MTR-004217",
   "asset_type": "meter",
   "location": {
    "lat": 51.5,
    "lon": 26.0254,
    "zone_id": "B-S6",
    "county": "București",
    "label": "Contor MTR-004217"
   },
   "target_date": "2026-11-09",
   "prediction": {
    "model_id": "a-lgbm",
    "model_version": "a-lgbm@fixture",
    "prediction_id": "69136ff3-7a5a-454f-a9a6-727700efb5ea",
    "label": "tamper",
    "score": 1.4,
    "interval_low": 0.69,
    "interval_high": 0.95,
    "confidence": "high",
    "abstain": false,
    "abstain_reason": null
   },
   "impact": {
    "expected_value_lei": 1239.75,
    "value_if_true_lei": 1425.0,
    "customers_affected": 1,
    "urgency_hours": 72,
    "safety_flag": true,
    "assumptions_ref": "meters"
   },
   "effort": {
    "duration_min": 40,
    "crew_skill": "metering",
    "crew_size": 2,
    "requires_planned_outage": false
   },
   "explanation": {
    "top_factors": [
     {
      "feature": "zero_run_days_30d",
      "label_ro": "9 zile la rând cu consum zero",
      "value": 9,
      "contribution": 0.31
     },
     {
      "feature": "peer_ratio_post",
      "label_ro": "cu 72% sub vecinii de pe același post",
      "value": 0.28,
      "contribution": 0.22
     }
    ],
    "similar_cases": [
     {
      "case_id": "SGCC-0193",
      "outcome": "furt_confirmat",
      "similarity": 0.91
     }
    ],
    "summary_ro": "Consum zero 9 zile după un istoric stabil și mult sub vecini. Merită verificat la fața locului."
   },
   "data_quality": {
    "missing_ratio": 0.04,
    "input_issues": [],
    "synthetic": true,
    "data_sources": [
     "fixture ilustrativ"
    ]
   },
   "recommended_action": "inspect_on_site",
   "created_at": "2026-11-08T06:00:00+02:00",
   "extra": {
    "series_ref": "outputs/series/A/MTR-004217.json"
   }
  }
 ],
 "audit": [
  {
   "audit_id": "e8d43cf9-6bf3-4b30-8e5e-dd4a7cb6eb3f",
   "ts": "2026-11-08T06:00:00+02:00",
   "actor": "agent",
   "action": "assigned",
   "work_item_id": "A-20261109-MTR-004217",
   "prediction_id": "69136ff3-7a5a-454f-a9a6-727700efb5ea",
   "model_version": "a-lgbm@fixture",
   "rule_id": "R-VALUE-OVER-COST",
   "threshold": {
    "min_net_value_lei": 0.0
   },
   "inputs_sha256": null,
   "note": null
  },
  {
   "audit_id": "2c90a4cf-0626-4bae-a6ae-0ad3121b8e44",
   "ts": "2026-11-08T06:00:00+02:00",
   "actor": "agent",
   "action": "assigned",
   "work_item_id": "C-20261109-PT-1432",
   "prediction_id": "890a27e2-c5c0-452b-bda8-a79bd50db55c",
   "model_version": "c-lgbm@fixture",
   "rule_id": "R-VALUE-OVER-COST",
   "threshold": {
    "min_net_value_lei": 0.0
   },
   "inputs_sha256": null,
   "note": null
  },
  {
   "audit_id": "73600e48-4c2a-4ab6-bc8c-2eb0e283083a",
   "ts": "2026-11-08T06:00:00+02:00",
   "actor": "agent",
   "action": "assigned",
   "work_item_id": "A-20261109-MTR-019833",
   "prediction_id": "9a3fd03f-3fc6-43ad-a041-ca5fcb97e7e8",
   "model_version": "a-lgbm@fixture",
   "rule_id": "R-VALUE-OVER-COST",
   "threshold": {
    "min_net_value_lei": 0.0
   },
   "inputs_sha256": null,
   "note": null
  },
  {
   "audit_id": "4285add9-20f9-4885-89d6-00d945b024e8",
   "ts": "2026-11-08T06:00:00+02:00",
   "actor": "agent",
   "action": "human_review",
   "work_item_id": "A-20261109-MTR-027710",
   "prediction_id": null,
   "model_version": null,
   "rule_id": null,
   "threshold": {},
   "inputs_sha256": null,
   "note": null
  }
 ],
 "depots": [
  {
   "depot_id": "D-BUC-V",
   "label_ro": "Bază operativă București Vest (simulată)",
   "lat": 44.4355,
   "lon": 26.016,
   "region": "muntenia_sud"
  },
  {
   "depot_id": "D-BUC-E",
   "label_ro": "Bază operativă București Est (simulată)",
   "lat": 44.431,
   "lon": 26.165,
   "region": "muntenia_sud"
  },
  {
   "depot_id": "D-CTA",
   "label_ro": "Bază operativă Constanța (simulată)",
   "lat": 44.1733,
   "lon": 28.6383,
   "region": "dobrogea"
  },
  {
   "depot_id": "D-TM",
   "label_ro": "Bază operativă Timișoara (simulată)",
   "lat": 45.7537,
   "lon": 21.2257,
   "region": "banat"
  }
 ],
 "regions": {
  "muntenia_sud": {
   "label_ro": "Muntenia Sud",
   "counties": [
    "București",
    "Ilfov",
    "Giurgiu"
   ]
  },
  "dobrogea": {
   "label_ro": "Dobrogea",
   "counties": [
    "Constanța",
    "Tulcea",
    "Călărași",
    "Ialomița"
   ]
  },
  "banat": {
   "label_ro": "Banat",
   "counties": [
    "Timiș",
    "Arad",
    "Caraș-Severin",
    "Hunedoara"
   ]
  }
 },
 "crews": [
  {
   "crew_id": "E-BV-1",
   "depot_id": "D-BUC-V",
   "skills": [
    "metering"
   ],
   "size": 2
  },
  {
   "crew_id": "E-BV-2",
   "depot_id": "D-BUC-V",
   "skills": [
    "metering",
    "lv_grid"
   ],
   "size": 2
  },
  {
   "crew_id": "E-BV-3",
   "depot_id": "D-BUC-V",
   "skills": [
    "lv_grid",
    "mv_grid"
   ],
   "size": 3
  },
  {
   "crew_id": "E-BE-1",
   "depot_id": "D-BUC-E",
   "skills": [
    "metering"
   ],
   "size": 2
  },
  {
   "crew_id": "E-BE-2",
   "depot_id": "D-BUC-E",
   "skills": [
    "lv_grid",
    "mv_grid"
   ],
   "size": 3
  },
  {
   "crew_id": "E-CT-1",
   "depot_id": "D-CTA",
   "skills": [
    "lv_grid",
    "mv_grid"
   ],
   "size": 3
  },
  {
   "crew_id": "E-CT-2",
   "depot_id": "D-CTA",
   "skills": [
    "metering",
    "lv_grid"
   ],
   "size": 2
  },
  {
   "crew_id": "E-TM-1",
   "depot_id": "D-TM",
   "skills": [
    "lv_grid",
    "mv_grid"
   ],
   "size": 3
  }
 ],
 "shift": {
  "start": "08:00",
  "end": "16:00"
 }
};
