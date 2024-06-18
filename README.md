# BotHub-server

## Server Architecture
![](https://sun9-63.userapi.com/impg/ADTAsBJuR0-TvXZj3PXDWLIZpMLs6GFiY8AqjQ/Z1nGVUCr_aE.jpg?size=868x586&quality=96&sign=cb61f0186f24d422221ce4f18c87a847&type=album)
- (Web impl. is not available)


A simple server for testing local self-written games and bots in the form of modules with Docker.

Also check [Bothub-client](https://github.com/PrefectSol/BotHub-client.git) for using server

## Install
Make sure you have a docker
```bash
git clone https://github.com/PrefectSol/BotHub-server.git
cd BotHub
make build
```

## Start server
The server will exist as a file `.platform`
```bash
make start
```
 - The file `platform/platform-config.json` is used for configuration

## Stop server
The server file will be deleted
```bash
make stop
```

## Status
Shows the contents of the file .platform
```bash
make status
```

## Enable network module
It includes a network interaction module. Disabled by default
```bash
make enable-net
```

## Disable network module
Network requests to the server are no longer available
```bash
make disable-net
```

## Clear database
Deletes the entire database
```bash
make rmdb
```

## Clear solution
```bash
make clear
```