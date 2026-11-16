FROM python:3.10.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System packages: Java + libraries the Unity Linux player needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk-headless \
    libglib2.0-0 \
    libgl1 \
    libdbus-1-3 \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Constraints apply to every pip command below
COPY constraints.txt .
ENV PIP_CONSTRAINT=/app/constraints.txt

# Build tooling (setuptools pinned via constraints, keeps pkg_resources)
RUN pip install setuptools==69.5.1 wheel

# CPU-only PyTorch (PyTorch index is only used for torch itself)
RUN pip install torch==2.1.2+cpu --extra-index-url https://download.pytorch.org/whl/cpu

# ML-Agents: let pip resolve its own declared dependencies
RUN pip install mlagents==1.0.0 mlagents-envs==1.0.0

# Your CSV plugin (no-deps so it cannot change anything above)
COPY ml-agents/csv-plugin ./csv-plugin
RUN pip install --no-deps ./csv-plugin

# Fail the build now if anything is inconsistent
RUN pip check; \
    python -c "import numpy, google.protobuf, torch, onnx, h5py, pkg_resources, mlagents, mlagents_envs; \
print('numpy', numpy.__version__, '| protobuf', google.protobuf.__version__, '| torch', torch.__version__)" \
 && mlagents-learn --help > /dev/null

# Java launcher + hyperparameter tools
COPY ml-agents/Project/Automation/src/MLAgentLauncher.java ./launcher/
COPY ml-agents/Project/Automation/randomizer/*.py ./randomizer/
RUN javac -d launcher launcher/MLAgentLauncher.java

# Unity Linux build + training configs
COPY app_Builds/3dballLinux ./env
RUN chmod -R +x ./env
COPY ml-agents/config ./config

VOLUME /app/results

ENTRYPOINT ["java", "-cp", "/app/launcher", "MLAgentLauncher"]
CMD ["5", "/app/config/ppo/3DBall.yaml", "/app/env/3dBallLinux.x86_64"]