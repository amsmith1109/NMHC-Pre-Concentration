[
"cool down",
"trap power check",
{"name": "flush",
    "valves":      [0,0,0,0,0],
    "aux1":        1,
    "sample":      100,
    "pump":        1,
    "condition":   "time",
    "value":       0.75
    },
{"name": "bleed pressure",
    "aux1":        0,
    "condition":   "time",
    "value":       0.1
    },
{"name": "sampling",
    "valves":     [0,1,0,0,0],
    "condition":  "time",
    "aux2":       1,
    "value":      20
    },
{"name": "sampling end",
    "valves":     [0,0,0,0,0],
    "aux2":       0
    },
"pre-backflush",
"backflush",
"drop backflush",
"isolate trap",
"check gc",
"flash heat",
"check heater",
"start gc",
"inject",
"bake out",
"post bake",
"off"
]
