1

/app/config/ppo/3Dball.yaml

/app/env/3dBallLinux.x86_64

MLAgentLauncher

java -cp launcher MLAgentLauncher 1 /app/config/ppo/3DBall.yaml /app/env/3dBallLinux.x86_64

  

Build : docker build --platform linux/amd64 -t ml-trainer:latest .

  

Run :  docker run --rm -it --platform linux/amd64 ml-trainer:latest bash

  

  

- pkg ressources

-  protobuf package to 3.20.x or lower.

The aliases was originally deprecated in NumPy 1.20; for more details and guidance see the original release note at:

## Current DOckerfile
FROM python:3.10.12-slim-bookworm

  

RUN apt-get update && apt-get install -y --no-install-recommends \

default-jdk-headless \

&& rm -rf /var/lib/apt/lists/*

  

WORKDIR /app

  
  

COPY app_Builds/3dballLinux ./env

RUN chmod -R +x ./env

  

# Training configs

COPY ml-agents/config ./config

  

COPY requirements.txt .

RUN pip install --no-cache-dir "setuptools<81" wheel \

&& pip install --no-cache-dir torch==2.14.0 --extra-index-url https://download.pytorch.org/whl/cpu \

&& pip install --no-cache-dir -r requirements.txt \

&& pip install --no-cache-dir --no-deps onnx==1.13.1 protobuf==7.36.2 \

&& pip install --no-cache-dir --no-deps numpy==1.26.4 ml-dtypes==0.5.1\

&& pip install --no-cache-dir --no-deps mlagents==1.0.0 mlagents-envs==1.0.0

  

COPY ml-agents/Project/Automation/src/MLAgentLauncher.java ./launcher/

COPY ml-agents/Project/Automation/randomizer/*.py ./randomizer/

RUN javac -d launcher launcher/MLAgentLauncher.java

  

COPY ml-agents/csv-plugin ./csv-plugin

RUN pip install --no-cache-dir --no-deps ./csv-plugin

CMD ["java", "-cp", "launcher", "MLAgentLauncher"]

  

% java MLAgentLauncher 1 /app/config/ppo/3Dball.yaml /app/env/3dBallLinux.x86_64

## Requirements 
absl-py==2.5.0

anyio==4.15.1

attrs==26.1.0

cattrs==1.5.0

certifi==2026.7.22

click==8.5.0

cloudpickle==3.1.2

exceptiongroup==1.3.1

filelock==3.32.7

fsspec==2026.7.0

grpcio==1.48.2

gym==0.26.2

gym-notices==0.1.0

h11==0.16.0

h5py==3.8.0

hf-xet==1.6.0

httpcore==1.0.9

httpx==0.28.1

huggingface-hub==1.32.0

idna==3.20

jinja2==3.1.6

markdown==3.10.3

markupsafe==3.0.3

mpmath==1.3.0

networkx==3.4.2

onnx-ir==1.1.0

onnxscript==0.7.2

packaging==26.3

pettingzoo==1.15.0

pillow==12.3.0

pyyaml==6.0.3

setuptools==80.10.2

six==1.17.0

sympy==1.14.0

tensorboard==2.20.0

tensorboard-data-server==0.7.2

tomli==2.4.1

tqdm==4.70.1

typing-extensions==4.16.0

werkzeug==3.1.8