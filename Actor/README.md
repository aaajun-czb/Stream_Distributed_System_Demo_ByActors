## Make the proto
```
python3  -m  grpc_tools.protoc  --python_out=./  --grpc_python_out=./  -I./ code.proto
```


## Run the Actor Server

```
python main.py
```

## Run the Task

```
python App.py
```

## Something about it

The services used by Actor Application need to be written and started in advance.
Yes, I have started the service running in Actor in advance. If you need to start it after notification, please feel free to modify it.