[
{"name":	"pre-backflush",
"valves": 	[0,0,1,0,0],
"backflush":	50,
"pump":		1,
"condition":	"time",
"value":   	0.25}
,
{"name":	"backflush",
"valves": 	[0,1,1,0,0],
"pump":		1,
"condition":	"time",
"value":   	0.5}
,
{"name":	"flash heat",
"valves": 	[0,1,1,0,0],
"ads":    	300,
"pump":		1}
,
{"name":        "check heater",
"ads":          275,
"condition":    "temp",
"value":        ">",
"timeout":      0.15}
,
{"name":	"set cool down",
"valves": 	[0,1,1,0,1],
"ads":    	-99,
"pump":		1
},
{"name":	"check room temp",
"ads":    	20,
"condition":	"temp",
"value":   	"<"}
,
{"name":	"off",
"valves": 	[0,0,0,0,0],
"backflush":	0,
"pump":		0}
]
