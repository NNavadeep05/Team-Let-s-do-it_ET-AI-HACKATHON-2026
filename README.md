# NEURON IQ

Every Answer. Every Asset. Always Connected.

## Overview
NEURON IQ is an industrial knowledge intelligence engine for plant operations. It integrates documents, piping & instrumentation diagrams (P&IDs), maintenance history, regulations, and tribal knowledge into a single unified knowledge graph.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (npm)

### Bootstrapping the System
To spin up all services, run database migrations, seed the ontology constraints, initialize the Qdrant collections, and load the curated demo dataset:

```bash
make bootstrap
```

### Services
- **Web Dashboard**: http://localhost:5173
- **FastAPI Backend**: http://localhost:8000/api
- **Neo4j Browser**: http://localhost:7474
- **Qdrant Dashboard**: http://localhost:6333
- **MinIO Console**: http://localhost:9001
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
