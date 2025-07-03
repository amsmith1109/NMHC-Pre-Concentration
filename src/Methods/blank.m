[
"cool down",
{
    "name":        "flush",
    "valves":      [0, 0, 1, 0, 0],
    "backflush":      100,
    "pump":        1,
    "condition":   "time",
    "value":       0.5},
{
    "name":        "sampling",
    "valves":      [0, 1, 0, 0, 0],
    "pump":        1,
    "condition":   "pulse",
    "value":       20.0,
    "monitor":     true},
{
    "name":        "pressurize trap",
    "valves":      [0, 1, 1, 1, 0],
    "backflush":   25},
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
