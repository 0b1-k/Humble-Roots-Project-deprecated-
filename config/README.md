# Humble Roots Project Configuration

As mentioned in the [project overview](../docs/HumbleRootsProject.pdf), the software driving the automation is composed of several modules (blue circles in the architecture diagram below), each running within its own process. The modules communicate with each other by publishing messages to various topics through an [MQTT broker](http://mqtt.org/). Based on their function, the modules also subscribe to topics of interest and react whenever messages are being published.

## Architecture Diagram

![Architecture](../docs/architecture.png "Architecture")

## First time installation

Out of the box, the project provides two template configuration files that must be renamed and edited for the project to work.
This ensures that future project updates will not destroy your local configuration.

This only needs to be done once.

1. Switch to the '/config' project folder.
2. Copy ['bootstrap.json.template'](./bootstrap.json.template) to 'bootstrap.json'
3. Copy ['config.json.template'](./config.json.template) to 'config.json'

## The role of the 'bootstrap.json' configuration file

The role of 'bootstrap.json' is to allow distributed modules to find and connect to an MQTT broker.
The exception to this is the *Control* process.
By default, the MQTT broker is expected to be located on the local host.
Once a process is connected to its MQTT broker, it receives its configuration settings by subscribing to the 'config' MQTT topic managed centrally by the *Control* process.

### 'mqtt' section

This is the only section in this configuration file. It should reflect the connection settings defined for the MQTT broker itself.

```
{
"mqtt": {
	"host": "localhost",
	"port": 1883,
	"keepalive": 60,
	"rootPrefix": "hrs"
	}
}
```

**Security Warning**: there's currently no security measures in place to secure connections to the MQTT broker. This will be adressed in the near future, but in the meantime, the MQTT broker and the *Humble Roots Project* processes should all run on the same local machine, preferably on an isolated, secured network segment. In addition, external connections to the MQTT broker should be blocked by a firewall on the local host. **Under no circumstances should the MQTT broker be exposed to the Internet unsecured**. For details on **how to secure MQTT**, check out this excellent [series of articles](http://www.hivemq.com/mqtt-security-fundamentals-wrap-up) written by the folks at HiveMQ.

## The role of the 'config.json' configuration file

The 'config.json' file holds the settings used by the various *Humble Roots Project* modules.
Whenever the 'config.json' is updated, the *Control* module detects the change and publishes the content of the file on the 'config' topic, thereby making it available to the other application modules.
This method of distributing configuration settings is necessary when the modules are distributed on separate systems.

The 'config.json' file is composed of several setting sections and sub-sections driving the different features of the project, as described below.

There are two types of settings:

1. Module-specific configuration settings
2. User-defined rules

Please refer to the [user-defined rules document](./rules.md) to understand how they work.

When the *Control* module is provided with a [plant growth recipe](../recipe/EnigmaGirls2.csv), it also generates automation rules on the fly.
Please note that this feature is not part of the v0.4 release.

### "mqtt" section

This section is used by all the application modules to connect to the MQTT broker after bootstrapping themselves. It is identical to the MQTT settings in the 'bootstrap.json' file. If the MQTT settings change here, the same changes must to be applied to the 'bootstrap.json' file(s).

```
"mqtt": {
	"host": "localhost",
	"port": 1883,
	"keepalive": 60,
	"rootPrefix": "hrs"
	},
```

"rootPrefix": defines a namespace for all the subtopics used by the application.

This allows for multiple instances of the project to run side-by-side on the same broker, as needed.

### "serial" section

This section is used by the *Gateway* module to communicate with the *gateway* node over a serial port.

```
"serial": {
	"port": "/dev/ttyUSB0",
	"baudrate": 115200,
	"pubPrefix": "ser",
	"subPrefix": "cmd"
	},
```

"port": specifies the device attached to the *gateway* node. It is set to "/dev/ttyUSB0" by default but this may vary if other serial devices are connected to the machine.

"baudrate": By default, the "baudrate" is set to match the speed of the *gateway* node.

"pubPrefix": specifies the topic under which the *Gateway* module publishes data coming from the *gateway* node.

"subPrefix": specifies the topic where the *Control* module publishes commands to be sent to the wireless nodes through the *gateway* node.

### "influxDB" section

This section is used by the *DB* module which writes sensor data to the InfluxDB database.

```
"influxDB": {
	"enabled": 0,
	"host": "localhost",
	"port": 8086,
	"user": "<DB USER>",
	"pswd": "<DB PSWD>",
	"db": "sensors"
	},
```

"enabled": by default, the feature is disabled. Set it to 1 to enable it when InfluxDB is up and running.

"host": specifies the domain name or IP address of the host running InfluxDB. By default, this is the local host.

"port": specifies the port number where InfluxDB listens for REST API calls.

"user": specifies the user to be used for authenticating to the InfluxDB instance.

"pswd": specifies the password of the user.

"db": specifies the name of the database where incoming sensor data should be written.

### "PushBullet" section

This section is used by the *Notify* module which handles push notifications between mobile devices and the application using the [PushBullet API](https://docs.pushbullet.com/).

```
"PushBullet": {
	"enabled": 0,
	"token": "<YOUR APPLICATION TOKEN>",
	"appDevice": "HumbleRoots",
	"alertDevice": "<MOBILE DEVICE PB ID>",
	"alertNumber": "+1 425 555 1212",
	"subPrefix": "notify",
	"accept": {"note": 0, "alert": 0}
	},
```

"enabled": by default, the feature is disabled. Set it to 1 to enable it once your PushBullet account is created and configured.

"token": every application using the PushBullet API requires a unique token. To generate this token, simple go to the [PushBullet account page](https://www.pushbullet.com/account) and copy the **Access Token** shown on the page. Then, simply paste the token here between the double quotes.

"appDevice": specifies an arbitratry device name representing the *Humble Roots Project* application. The push notifications emitted by the application will show up under this device name.

"alertDevice": specifies the ID of the mobile device registered with PushBullet that will be used to send SMS messages (Android only, at the moment). You can find a list of the devices registered with PushBullet under the [Devices account page](https://www.pushbullet.com/edit-devices).

"alertNumber": specifies the target phone number for the SMS messages which should be phone number of the device specified as the "alertDevice" above.

"subPrefix": specifies the topic subscribed to by the *Notify* module in order to send notifications as SMS messages to the "alertDevice" or as push notifications to the "appDevice".

"accept": specifies the types of messages supported by the *Notify* module. Messages of type "note" are forwarded to the "appDevice" while messages of type "alert" are forwarded to the "alertDevice".

### "sensorDataParser" section

This section is used by several of the application modules, such as the *DB* module in order to only accept relevant sensor data messages.
As new device types get added to the sensor and actuator network, they need to be listed here.

```
"sensorDataParser": {
	"accept": {"srh": 0, "lvl": 0, "clm": 0, "rly": 0, "vlv": 0}
	},
```

### "node" section

This section maps wireless node identifiers to friendly names.
As new devices get added to the sensor and actuator network, they need to be listed here.
Note that **the friendly names must be unique** just like their corresponding ID.

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

### "r" section

This section maps the IDs of the power outlets used by the *relay* actuator node to friendly names.
Note that **the friendly names must be unique** just like their corresponding ID.

```
"r":	{
	"0": "dh",
	"1": "drain",
	"2": "vent",
	"3": "water",
	"4": "light",
	"5": "air"
	},
```
### "v" section.

This section maps the IDs of the contacts used by the *valve* actuator node to friendly names.
Note that **the friendly names must be unique** just like their corresponding ID.

```
"v":	{
	"0": "filter",
	"1": "v1",
	"2": "v2",
	"3": "v3",
	"4": "v4",
	"5": "v5",
	"6": "v6",
	"7": "v7"
	},
```

### "s" section

This section maps the state zero and one to their corresponding OFF and ON friendly names.
This is used in context with actuator nodes, such as the *relay* and the *valve*, to express the state of the actuators.
Note that **the friendly names must be unique** just like their corresponding ID.

```
"s":	{
	"0": "off",
	"1": "on"
	},
```

### "control" section

This section is used by the *Control* module which evaluates incoming sensor data against user-defined rules and reacts by issuing commands to the actuators driving the automation.
It is broken down into the following sub-sections:

#### "config" sub-section

Specifies the topic used to publish the content of the 'config.json' file to the application processes.

```
	"config": {
		"subPrefix": "config"
		},
```

#### "tick" sub-section

Specifies the frequency in seconds at which the *Control* module evaluates time-based rules defined in the "timers" sub-section.
Ticks appear as Unix epoch timestamps on the "time" topic such as "ts=1435267471".

```
	"tick": {
		"freqSec": 30,
		"subPrefix": "time"
		},
```

#### "nodeTimeout" sub-section

Specifies the timeout duration in seconds before a wireless node is deemed "offline".
The *Control* module monitors the time interval between two messages sent by the nodes on the wireless network. If that interval exceeds the specified timeout duration, an SMS alert is fired off to "alertDevice" defined in the "PushBullet" section. The title of the SMS alert is defined by the "title" setting.

```
	"nodeTimeout": {
		"freqSec": 180,
		"title": "Signal lost"
		},
```
#### "command" sub-section

Specifies if the *Control* module should accept external commands.

Valid external commands can take two forms:

1. Commands directed to wireless actuators such as "node=relay&cmd=act&r=light&s=on" or "node=valve&cmd=act&v=filter&s=on"
2. Command requesting a report such as "get=report"

External commands are currently handled through the *Notify* module, which relies on the [PushBullet API](https://www.pushbullet.com/get-started).
Please refer to the [dependencies document](../dependencies.md) for details on installing and configuring *PushBullet*, *IFTTT* and *IFTTT's Do Button* on a mobile device to send commands to the application.

```
	"command": {
		"enabled": 1,
		"subPrefix": "shell",
		"report": {"enabled": 1}
		},
```

"subPrefix": specifies the topic used to publish command to the *Control* module.

"report": {"enabled": 1} enables the reporting feature. {"enabled": 0} disables it.

#### "signal" rules sub-section

This section is used to monitor the signal strength of all wireless nodes.
If the signal strength of a given node drops below the specified decibel level, an alert is fired off once.
An alert is also fired off once when the signal strength of that same node "recovers" from being too low.

```
	"signal": [{
		"enabled": 1,
		"value": "rssi",
		"alert": {"op": "<", "setpoint": -80.0, "title": "Low signal strength alert"}
		}],
```

#### "srh" rules sub-section

This section is used to evaluate sensor data of type "srh", which stands for "Soil Relative Humidity".

This rule drives the irrigation system, and is only activated between 7pm and 8pm. During that time interval, the rule checks the relative humidity of the soil as reported by the "plant" node and turns "on" the relay driving the irrigation pump if the moisture level of the soil is below 85%. The irrigation relay is turned "off" when the time window closes or when the relative soil moisture reaches the setpoint.

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
#### "lvl" rules sub-section

This section is used to evaluate sensor data of type "lvl", which stands for "Level".

This rule turns the sump pump "on" when the water level reported by the "sump" node is 22.1cm away from the ultrasonic sensor.
The pump is turned "off" when the water level drops back down sufficiently. In this instance, the stopping point is set at 26.5cm away from the ultrasonic sensor.
In addition, the rule defines an "alert" level which would fire if the sump pump were to fail, for example.

```
	"lvl": [{
		"enabled": 1,
		"node": "sump",
		"value": "cm",
		"on":  {"op": "<=", "setpoint": 22.1, "cmd": "node=relay&cmd=act&r=drain&s=on"},
		"off": {"op": ">=", "setpoint": 26.5, "cmd": "node=relay&cmd=act&r=drain&s=off"},
		"alert": {"op": "<=", "setpoint": 21.0, "title": "High water level alert"}
		}],
```

#### "clm" rules sub-section

This section is used to evaluate sensor data of type "clm", which stands for "Climate".

In this example, two rules are defined since the "climate" node emits distinct data points, respectively "tmp" for "temperature" and "rh" for "relative humidity".
Both rules also define alert thresholds should the ventilation fan or the dehumidifier fail.

```
	"clm": [{
		"enabled": 1,
		"node": "climate",
		"value": "tmp",
		"on":  {"op": ">",  "setpoint": 25.6, "cmd": "node=relay&cmd=act&r=vent&s=on"},
		"off": {"cmd": "node=relay&cmd=act&r=vent&s=off"},
		"alert": {"op": ">=", "setpoint": 30.0, "title": "High temperature alert"}
		},
		{
		"enabled": 1,
		"node": "climate",
		"value": "rh",
		"on":  {"op": ">",  "setpoint": 54.0, "cmd": "node=relay&cmd=act&r=dh&s=on"},
		"off": {"cmd": "node=relay&cmd=act&r=dh&s=off"},
		"alert": {"op": ">=", "setpoint": 56.0, "title": "High humidity alert"}
		}],
```

#### "timers" rules sub-section

Timer are triggered on a regular basis by the *Control* module (see the "tick" sub-section above) as opposed to being triggered by incoming sensor data.
Timer rule define a "task" name which must be unique.

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

### "report" section

This section is used internally by the *Control* module when processing a report request.
The report is composed dynamically from cached sensor and actuator data.
The cached data is accessed through the report template directives defined in this section.
The report is sent as a push notification to the "appDevice" defined in the "PushBullet" section.

```
"report": {
	"enabled": 1,
	"title": "Current State",
	"divider": "~",
	"node": {
		"plant": [
			{"value": "p", "label": "Soil RH", "unit": "%"},
			{"value": "rssi", "label": "Signal", "unit": "dB"}
			],
		"climate": [
			{"value": "tmp", "label": "Temp", "unit": "C"},
			{"value": "rh", "label": "RH", "unit": "%"},
			{"value": "rssi", "label": "Signal", "unit": "dB"}
			],
		"sump": [
			{"value": "cm", "label": "Depth", "unit": "cm"},
			{"value": "rssi", "label": "Signal", "unit": "dB"}
			],
		"relay": [
			{"value": "r", "state": "s"},
			{"value": "rssi", "label": "Signal", "unit": "dB"}
			],
		"valve": [
			{"value": "v", "state": "s"},
			{"value": "rssi", "label": "Signal", "unit": "dB"}
			]
		}
	}
```
