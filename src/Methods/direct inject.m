["off",
"check gc"
,
{"name":		"sample",
"valves":		[0,0,0,1,0],
"sample":		50,
"pump":			0,
"condition":	"time",
"value":		1}
,
{"name":		"depressurize loop",
"sample":		0,
"condition":	"time",
"value":		0.15}
,
{"name":		"inject",
"valves":		[1,0,0,0,0],
"condition":	"gc",
"value":		1}
,
"off"
]
