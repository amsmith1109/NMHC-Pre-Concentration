[
{"name":        "pre-backflush",
"valves":       [0,0,1,0,0],
"backflush":	100,
"pump":		1,
"condition":	"time",
"value":	0.25
},
{"name":        "backflush",
"valves":	[0,1,1,0,0],
"condition":	"time",
"value":	0.5
},
{"name":        "heat Trap",
"valves":	[0,1,1,0,0],
"ads":          300
},
"check heater",
{"name":        "bake out",
"condition":	"time",
"value":	2
},
"post bake"
,
"off"
]
