## Make the proto
```
python3  -m  grpc_tools.protoc  --python_out=./  --grpc_python_out=./  -I./ code.proto
```


## Run the Master Server

```
python main.py
```