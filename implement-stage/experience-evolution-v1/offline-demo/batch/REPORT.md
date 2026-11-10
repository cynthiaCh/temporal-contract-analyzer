# Expert-gated evolution

This is a bounded development/evaluation execution record. Expert activation is a separate operator action.

```json
{
  "status": "awaiting_expert",
  "backend_kind": "synthetic_fixture_not_model_or_effectiveness_evidence",
  "kind": "development",
  "actual_model_execution": false,
  "planned": 5,
  "started": 5,
  "valid": 5,
  "invalid": 0,
  "unstarted": 0,
  "behavior_vectors": {
    "BASE-1": {
      "missing_required_effects": [
        "retirement"
      ],
      "observed_effects": {
        "ordering": true,
        "preserved": true,
        "retirement": false
      },
      "observed_forbidden_effects": [],
      "origin": "synthetic_fixture_not_real_behavior_result",
      "schedules": {
        "synthetic": {
          "checks": [
            {
              "actual": false,
              "expected": false,
              "passed": true
            }
          ]
        }
      },
      "verdict": "UNDERREACH"
    },
    "BASE-2": {
      "missing_required_effects": [
        "retirement"
      ],
      "observed_effects": {
        "ordering": true,
        "preserved": true,
        "retirement": false
      },
      "observed_forbidden_effects": [],
      "origin": "synthetic_fixture_not_real_behavior_result",
      "schedules": {
        "synthetic": {
          "checks": [
            {
              "actual": false,
              "expected": false,
              "passed": true
            }
          ]
        }
      },
      "verdict": "UNDERREACH"
    },
    "R1-DEV-1": {
      "missing_required_effects": [],
      "observed_effects": {
        "ordering": true,
        "preserved": true,
        "retirement": true
      },
      "observed_forbidden_effects": [],
      "origin": "synthetic_fixture_not_real_behavior_result",
      "schedules": {
        "synthetic": {
          "checks": [
            {
              "actual": false,
              "expected": false,
              "passed": true
            }
          ]
        }
      },
      "verdict": "PASS"
    },
    "R1-DEV-2": {
      "missing_required_effects": [],
      "observed_effects": {
        "ordering": true,
        "preserved": true,
        "retirement": true
      },
      "observed_forbidden_effects": [],
      "origin": "synthetic_fixture_not_real_behavior_result",
      "schedules": {
        "synthetic": {
          "checks": [
            {
              "actual": false,
              "expected": false,
              "passed": true
            }
          ]
        }
      },
      "verdict": "PASS"
    }
  },
  "known_requests": 5,
  "sessions_with_unknown_requests": 0,
  "requests_with_unknown_token_usage": 5,
  "known_requests_with_unknown_token_usage": 5,
  "sessions_with_missing_usage_counter": 0,
  "groups": {
    "starting_AUTO": {
      "planned": 2,
      "started": 2,
      "valid_scores": 2,
      "invalid": 0,
      "unstarted": 0,
      "whole_passes": 0,
      "whole_pass_rate": 0.0
    },
    "R1-candidate": {
      "planned": 2,
      "started": 2,
      "valid_scores": 2,
      "invalid": 0,
      "unstarted": 0,
      "whole_passes": 2,
      "whole_pass_rate": 1.0
    }
  },
  "known_seconds": 0.02319500595331192,
  "sessions_with_unknown_seconds": 0,
  "token_cost": {
    "input_tokens": {
      "known_subtotal": null,
      "sessions_without_known_subtotal": 5,
      "full_total": null
    },
    "cached_input_tokens": {
      "known_subtotal": null,
      "sessions_without_known_subtotal": 5,
      "full_total": null
    },
    "output_tokens": {
      "known_subtotal": null,
      "sessions_without_known_subtotal": 5,
      "full_total": null
    },
    "reasoning_output_tokens": {
      "known_subtotal": null,
      "sessions_without_known_subtotal": 5,
      "full_total": null
    },
    "total_tokens": {
      "known_subtotal": null,
      "sessions_without_known_subtotal": 5,
      "full_total": null
    }
  },
  "usage": [
    {
      "slot": "BASE-1",
      "usage": {
        "requests_started": 1,
        "total_usage": null,
        "usage_unknown_requests": 1
      }
    },
    {
      "slot": "BASE-2",
      "usage": {
        "requests_started": 1,
        "total_usage": null,
        "usage_unknown_requests": 1
      }
    },
    {
      "slot": "R1-reflection",
      "usage": {
        "requests_started": 1,
        "total_usage": null,
        "usage_unknown_requests": 1
      }
    },
    {
      "slot": "R1-DEV-1",
      "usage": {
        "requests_started": 1,
        "total_usage": null,
        "usage_unknown_requests": 1
      }
    },
    {
      "slot": "R1-DEV-2",
      "usage": {
        "requests_started": 1,
        "total_usage": null,
        "usage_unknown_requests": 1
      }
    }
  ],
  "comparisons": [
    {
      "development": "R1-DEV-1",
      "gained": [
        "retirement"
      ],
      "lost": [],
      "retained": [
        "ordering",
        "preserved"
      ],
      "starting": "BASE-1",
      "unknown": []
    },
    {
      "development": "R1-DEV-1",
      "gained": [
        "retirement"
      ],
      "lost": [],
      "retained": [
        "ordering",
        "preserved"
      ],
      "starting": "BASE-2",
      "unknown": []
    },
    {
      "development": "R1-DEV-2",
      "gained": [
        "retirement"
      ],
      "lost": [],
      "retained": [
        "ordering",
        "preserved"
      ],
      "starting": "BASE-1",
      "unknown": []
    },
    {
      "development": "R1-DEV-2",
      "gained": [
        "retirement"
      ],
      "lost": [],
      "retained": [
        "ordering",
        "preserved"
      ],
      "starting": "BASE-2",
      "unknown": []
    }
  ],
  "no_generalization_claim": true,
  "no_test_feedback_learning": false
}
```
