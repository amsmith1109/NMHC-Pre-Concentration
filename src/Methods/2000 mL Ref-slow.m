[
"cool down",
{
    "name":        "flush",
    "valves":      [0, 0, 0, 0, 0],
    "sample":      40,
    "pump":        1,
    "condition":   "time",
    "value":       0.5},
{
    "name":        "sampling",
    "valves":      [0, 1, 0, 0, 0],
    "condition":   "pulse",
    "value":       50,
    "monitor":     true},
{
    "name":        "pre-backflush",
    "valves":      [0, 0, 1, 1, 0],
    "sample":      0,
    "backflush":   1000,
    "condition":   "time",
    "value":       0.25},
{
    "name":        "backflush",
    "valves":      [0, 1, 1, 1, 0],
    "condition":   "time",
    "value":       2},
{
    "name":        "drop backflush",
    "backflush":   0,
    "condition":   "time",
    "value":       0.5
},
{
    "name":        "isolate trap",
    "valves":      [0, 0, 1, 1, 0],
    "condition":   "time",
    "value":       0.05},
{
    "name":        "check GC",
    "valves":      [0, 0, 1, 1, 0],
    "condition":   "gc"},
{
    "name":        "flash heat",
    "valves":      [1, 0, 1, 1, 0],
    "ads":         320,
    "condition":   "time",
    "value":       0.1},
{
    "name":        "check heater",
    "ads":         275,
    "condition":   "temp",
    "value":       ">",
    "monitor":     true,
    "timeout":     0.15},
{
    "name":        "start GC",
    "valves":      [1, 0, 1, 1, 0],
    "condition":   "gc",
    "value":       0},
{
    "name":        "inject",
    "valves":      [1, 1, 1, 1, 0],
    "condition":   "time",
    "value":       0.5},
{
    "name":        "bake out",
    "valves":      [0, 1, 1, 0, 0],
    "ads":         295,
    "backflush":   1000,
    "condition":   "time",
    "value":       2},
"post bake",
{
    "name":        "2nd bake out",
    "valves":      [0, 1, 1, 0, 0],
    "ads":         280,
    "condition":   "time",
    "value":      2},
"post bake",
"off"
]
