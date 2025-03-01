FROM python:3.10-slim

LABEL maintainer="Long Hao <hal.long@outlook.com>"
LABEL description="Python bindings for the Dem Bones library"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libeigen3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the source code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Run tests
RUN pip install --no-cache-dir pytest pytest-cov numpy \
    && pytest tests/

# Set the entrypoint
ENTRYPOINT ["python", "-c", "import py_dem_bones; print(f'py-dem-bones {py_dem_bones.__version__} installed successfully')"]
