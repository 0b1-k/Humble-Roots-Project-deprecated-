# Humble Roots Project

## Automation Rules

The automation in the *Humble Roots Project* is event-driven: whenever the *Control* module receives sensor data such as

```
node=2&rssi=-62&t=srh&bat=4.61&low=0&pwr=1&p=41&ts=1436298975
```

or time-based notifications, such as

```
ts=1436299093
```

it matches the content of the notifications against a set of rules. The rules define what actions need to be executed, if any.
Optionally, a rule can specify attributes defining a specific time or a frequency when a rule should be evaluated or if
an alert should be sent in case a sensor reports abnormal data, for example.

### General Rule Processing Operations

Let's examing the content of a sensor data notification, such as

```
node=2&rssi=-62&t=srh&bat=4.61&low=0&pwr=1&p=41&ts=1436298975
```

The *Control* module breaks down such a data notification into a series of name-value pairs.
Each value name is used as a key, some of which are referenced explicitly within the rules.

```
node=2
rssi=-62
t=srh
bat=4.61
low=0
pwr=1
p=41
ts=1436298975
```

Let's break down the meaning of the pairs in this example.

**node=2**: '2' is the numerical ID of the sensor node referenced in the **"node"** section of the [config.json](./config.json.template) file, which
gets resolved to **"plant"** in this instance. This name-value pair is always present in sensor data notifications.

```
"node": {
	"2": "plant",
	"4": "sump",
	"20": "relay",
	"30": "tank",
	"40": "climate",
	"50": "valve"
	},
```

**rssi=-62**: -62 is the signal strength of the sensor node expressed in decibels.
This name-value pair is always present in sensor data notifications.

**t=srh**: 'srh' stands for *Soil Relative Humidity* and provides the sensor's data type.
The sensor data type is used internally to classify and access rules of the same type.
This name-value pair is always present in sensor data notifications.

**bat=4.61**: 4.61 is the current voltage level of the battery powering the sensor node.
This name-value pair is always present in sensor data notifications.

**low=0**: indicates if the battery level is low (1) or not (0).
This name-value pair is always present in sensor data notifications.

**pwr=1**: indicates if the sensor node is being powered from battery (0) or from power mains (1).
This name-value pair is always present in sensor data notifications.

**p=41**: *p* is the sensor data payload and is specific to the *srh* data type.
It provides the current relative soil humidity, expressed as a percentage.

**ts=1436298975**: is a timestamp expressed in seconds since the Unix epoch.
Timestamps are appended by the *Gateway* node to all sensor data as they're received.
This name-value pair is always present in sensor data notifications.

### Processing Sensor Data Notifications

Now, let's look at the way rules reference the name-value pairs described above. 

```
"srh": [{
        "enabled": 1,
        "node": "plant",
        "value": "p",
        "time": {"from": "19:00", "to": "20:00"},
        "on":  {"op": "<", "setpoint": 85.0, "cmd": "node=relay&cmd=act&r=water&s=on"},
        "off": {"cmd": "node=relay&cmd=act&r=water&s=off"}
        }],
```

**"srh"**: this section is an array of rules handling all sensor data notifications of type *srh*.

**"enabled"**: 0 = rule is disabled, 1 = rule is enabled.

**"node"**: the friendly name of the node as defined in the *node* section of the [config.json](./config.json.template) file.
For clarity's sake, automation rules should always reference sensor nodes by their friendly name instead of their ID.
For instance, writing *node=relay&cmd=act&r=water&s=on* is easier to read and less error-prone than *node=20&cmd=act&r=3&s=1*.

**"value"**: provides the name of the value that needs to be evaluated against the terms defined by the rule.
In our example sensor data notification, the *value* is *p* and it is equal to *41*.

**"time"**: indicates a timeframe during which the rule should be evaluated.
If the current local time does not fall within the timeframe, the rest of the terms in the rule are not evaluated. 
A time frame is expressed as a time range, starting with *from* and ending with *to*.
Both times are expressed over 24 hours.
The *time* attribute is optional.

**"on"**: the *on* clause specifies a command to be executed if the expression within the clause evaluates to *true*.
The *on* clause includes an optional logical operator *op* used to compare the sensor data *value*,
a *setpoint* operand against which the sensor data *value* will be compared and a command *cmd* to be executed if the expression
evaluates to *true*. If the *op* operator and the *setpoint* operand are omitted, the clause becomes unconditional.

Supported *op* operators are:

* == : equal to
* >= : greater than or equal to
* <= : lower than or equal to
* > : greater than
* < : lower than
* != : different than

**"off"**: the *off* clause is only evaluated if the expression in the *on* clause was evaluated to be *false*.
In that case, the *off* clause specifies a command to be executed if the expression within the clause evaluates to *true*.
The terms of the expression in an *off* clause are identical to those of the *on* clause.


In pseudo-code, the rule 

```
"value": "p",
"time": {"from": "19:00", "to": "20:00"},
"on":  {"op": "<", "setpoint": 85.0, "cmd": "node=relay&cmd=act&r=water&s=on"},
"off": {"cmd": "node=relay&cmd=act&r=water&s=off"}
```

gets evaluated as:

```
if (localtime >= time.from and localtime < time.to) {
    if (value(p) < 85.0) {
        send("node=relay&cmd=act&r=water&s=on")
    }
    else {
        send("node=relay&cmd=act&r=water&s=off")
    }
}
```

### Processing Timer Notifications

Timer notifications are generated on a regular basis by the *Control* module.
According to the frequency defined in the *tick* section of the (config.json.template)[./config.json.template] file.

Example: 

```
ts=1436299093
```

*ts* stands for 'timestamp' and is expressed in seconds since the Unix Epoch.
Whenever a timer notification is generated, the *Control* module handles them by evaluating the rules 
defined in the *timers* section of the (config.json.template)[./config.json.template] file.
Timer rules are identical to the rules used to handle sensor data notifications.
The only difference is that timer rules must provide a unique *task* name which is used internally by the application.

```
"timers": [{
        "enabled": 1,
        "task": "light",
        "value": "ts",
        "time": {"from": "18:00", "to": "06:00"},
        "on":  {"cmd": "node=relay&cmd=act&r=light&s=on"},
        "off": {"cmd": "node=relay&cmd=act&r=light&s=off"}
        }]
```
