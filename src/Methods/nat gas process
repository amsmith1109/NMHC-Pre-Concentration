[
{
"name":         "initial check",
"message":      "Verify the stream selector is on the correct port, the sample is attached and CLOSED."}
,
{
"name":	        "evacuating line",
"valves":	[0,0,0,0,0],
"pump":		1,
"sample":       1000,
"condition":	"time",
"value":	1.5}
,
{
"name":         "pre-flush check",
"sample":       0,
"condition":    "manual",
"message":      "Open sample canister."}
,
{
"name":	        "flush",
"valves":	[0,0,0,0,0],
"sample":	50,
"condition":	"time",
"value":	0.5}
,
"off"
,
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
