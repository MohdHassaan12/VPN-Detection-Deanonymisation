# VPN Detection & Deanonymisation: System Architecture

The following diagram comprehensively maps the end-to-end architecture of the VPN Detection & Deanonymisation project. It illustrates the data flow from raw packet ingestion, through model training on DigitalOcean, into the high-performance Inference API, and finally to the interactive React dashboard.

## Comprehensive Architecture Diagram

```mermaid
flowchart TD
    %% Define Styles
    classDef client fill:#d4edda,stroke:#28a745,stroke-width:2px;
    classDef infra fill:#cce5ff,stroke:#007bff,stroke-width:2px;
    classDef ml fill:#f8d7da,stroke:#dc3545,stroke-width:2px;
    classDef ui fill:#fff3cd,stroke:#ffc107,stroke-width:2px;
    classDef cloud fill:#e2e3e5,stroke:#6c757d,stroke-width:2px;

    %% 1. Data Source & Preprocessing
    subgraph DATA[1. Data Ingestion & Preprocessing]
        RAW[Raw Network Traffic / PCAP]
        PREP[pcap_to_packetblock.py\n(Preprocessing & Unification)]
        IMG[64x64 Packet-Block Images]
        FEAT[25+ Flow Features & Metadata]
        
        RAW --> PREP
        PREP --> IMG
        PREP --> FEAT
    end

    %% 2. Cloud Training (DigitalOcean)
    subgraph CLOUD[2. Model Training - DigitalOcean Cloud]
        TR_CNN[Train Stage 1: CNN App Classifier]
        TR_XGB[Train Stage 2: XGBoost Intent Classifier]
        MODELS[(Trained Models\n.h5 / .xgb)]
        
        IMG --> TR_CNN
        FEAT --> TR_XGB
        TR_CNN -->|Yields App_Class| TR_XGB
        TR_CNN --> MODELS
        TR_XGB --> MODELS
    end

    %% 3. Live Inference Pipeline (Backend)
    subgraph BACKEND[3. Live Inference Service - FastAPI & Docker]
        direction TB
        L1[Layer 1: Edge Firewall\nIP Intelligence, Fast block/pass]
        L2[Layer 2: Load Balancer / TLS Termination\nSNI, RTT, JA3 extraction]
        
        subgraph L3G[Layer 3: ML Risk Scoring Engine]
            S1[Stage 1: CNN App Classifier\nDetermines Application]
            S2[Stage 2: XGBoost Intent Classifier\nCalculates Risk Score 0-99]
            S1 --> |App_Class| S2
        end

        L4[Layer 4: Policy Engine\nEvaluates rules against Risk Score\nActions: ALLOW / CHALLENGE / BLOCK]
        
        REDIS[(Redis Cache\nIn-memory state & Stream data)]
        WS((WebSocket Server\nReal-time events))
        
        L1 --> L2
        L2 --> S1
        S2 --> L4
        L4 --> REDIS
        REDIS --> WS
    end

    %% 4. Dashboard (Frontend)
    subgraph FRONTEND[4. Frontend Dashboard - React/Vite]
        NGINX[Nginx Reverse Proxy / Router]
        UI_OVER[Overview / Health Metrics]
        UI_ANA[Analytics & Deanonymisation\nCharts & Tables]
        UI_POL[Policy Evaluation Engine]
        UI_SIM[Interactive Traffic Simulator]
        
        NGINX --> UI_OVER
        NGINX --> UI_ANA
        NGINX --> UI_POL
        NGINX --> UI_SIM
    end

    %% Connections across subgraphs
    DATA -.->|Prepares Data For| CLOUD
    MODELS == Loads At Startup ==> BACKEND
    
    TRAFFIC((Live Network Traffic)) --> L1
    
    WS == Sub-200ms Live Stream ==> NGINX
    NGINX <--> API{REST API} 
    API <--> BACKEND
    
    %% Apply classes
    class RAW,TRAFFIC client;
    class PREP,IMG,FEAT infra;
    class TR_CNN,TR_XGB,MODELS cloud;
    class L1,L2,L3G,S1,S2,L4 ml;
    class UI_OVER,UI_ANA,UI_POL,UI_SIM,NGINX ui;
```

### Flow Breakdown

1. **Data Ingestion & Preprocessing:** Raw PCAP files from multiple datasets (CIC IDS 2017, ISCX-VPN, etc.) are preprocessed. Payloads are transformed into `64x64x3` image blocks for CNNs, while time-series flow features and metadata (like JA3, SNI) are extracted for XGBoost.
2. **Cloud Training:** The processed data is pushed to DigitalOcean Droplets where models are trained. The 2-stage mechanism involves the CNN first classifying the application type, which is then fed into XGBoost along with other features to ascertain VPN intent and risk.
3. **Live Inference Pipeline:** A FastAPI application orchestrates a 4-layer inspection stack capable of sub-200ms latency. The risk calculations are logged and cached in **Redis** and constantly broadcasted via **WebSockets**.
4. **Frontend Dashboard:** A React frontend (styled dynamically and packaged with **Vite**) connects via Nginx to listen to the WebSocket stream, rendering live traffic analytics, enforcing limits, and providing a hands-on simulator.
