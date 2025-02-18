[
{"name":	"Initialize Off",
"valves":       [0,0,0,0,0],
"pump":		0,
"backflush":	0,
"sample":	0,
"ads":		-99,
"h2o":		-99,
"condition":    "manual",
"message":	"This method will allow you to check that each valve is working properly. Each valve will be returned to the 'off' position after it is checked. The system will automatically timeout after 5 minutes on each check."
},
{"name":	"Test valve 0",
"valves":       [1,0,0,0,0],
"condition":    "manual",
"message":	"Did valve 0 rotate?"
},
{"name":	"Test valve 1",
"valves":       [0,1,0,0,0],
"condition":    "manual",
"message":	"Did valve 1 rotate?"
},
{"name":	"Test valve 2",
"valves":       [0,0,1,0,0],
"condition":    "manual",
"message":	"Did valve 2 rotate?"
},
{"name":	"Test valve 3",
"valves":       [0,0,0,1,0],
"condition":    "manual",
"message":	"Did valve 3 rotate?"
},
{"name":	"Test valve 4",
"valves":       [0,0,0,0,1],
"condition":    "manual",
"message":	"Did valve 4 rotate?"
},
{"name":	"Test pump",
"valves":       [0,0,0,0,0],
"pump":		1,
"condition":    "manual",
"message":	"Is the pump on?"
},
{"name":	"off",
"pump":         0
}
]
