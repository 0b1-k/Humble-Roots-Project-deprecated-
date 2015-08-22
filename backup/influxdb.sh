#!/usr/bin/env bash
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/gocode

cd /home/gocode/src/github.com/eckardt/influxdb-backup/influxdb-dump
go run main.go -database climate -out /influxDB/climate.influxdb
go run main.go -database sensors -out /influxDB/sensors.influxdb

