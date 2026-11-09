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
RUN pip install --no-cache-dir torch==2.14.0 --extra-index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir --no-deps onnx==1.13.1 protobuf==3.20.3 \
 && pip install --no-cache-dir --no-deps mlagents==1.0.0 mlagents-envs==1.0.0

COPY ml-agents/Project/Automation/src/MLAgentLauncher.java ./launcher/
COPY ml-agents/Project/Automation/randomizer/*.py ./randomizer/
RUN javac -d launcher launcher/MLAgentLauncher.java

COPY ml-agents/csv-plugin ./csv-plugin
RUN pip install --no-cache-dir --no-deps ./csv-plugin
CMD ["java", "-cp", "launcher", "MLAgentLauncher"]