"""
Recruiter Market Matrix & Autonomous Domain Analyzer.
Covers the entire spectrum of tech recruiter demands (Cloud, DevOps, AI/ML, Full-Stack, Data Eng, Enterprise Backend, Systems, Security).
"""

RECRUITER_DOMAINS = {
    "Cloud & Infrastructure": [
        "AWS (EC2, S3, Lambda, RDS, IAM, ECS, EKS)",
        "Azure (App Services, Blob Storage, Azure Functions)",
        "Google Cloud Platform (GCP, BigQuery, GKE)",
        "Cloud Architecture & Serverless Computing"
    ],
    "DevOps & CI/CD": [
        "Docker & Containerization",
        "Kubernetes & Container Orchestration",
        "Terraform & Infrastructure as Code (IaC)",
        "GitHub Actions / Jenkins / GitLab CI/CD",
        "Linux / Bash Administration & Shell Scripting"
    ],
    "AI, Machine Learning & LLMs": [
        "Python (PyTorch, TensorFlow, Scikit-Learn)",
        "Generative AI & LLMs (Fine-tuning, Prompt Engineering)",
        "RAG Systems & Vector DBs (ChromaDB, Qdrant, PGVector, FAISS)",
        "NLP & Feature Engineering (TF-IDF, Tokenization, Embeddings)",
        "MLOps & Model Deployment (FastAPI, Triton, ONNX, MLflow)"
    ],
    "Full-Stack & Web Engineering": [
        "MERN Stack (MongoDB, Express.js, React.js, Node.js)",
        "Modern Web (Next.js, TypeScript, TailwindCSS, Redux)",
        "Python Web (Flask, Django, FastAPI)",
        "REST APIs & GraphQL Protocol",
        "WebSockets & Real-time Bi-directional Communication"
    ],
    "Enterprise Backend": [
        "Java (Core, Spring Boot, Spring Security, Hibernate/JPA)",
        "C# / .NET Core / ASP.NET",
        "Relational Databases (PostgreSQL, MySQL, SQL Query Tuning, Transactions)",
        "Microservices Architecture (API Gateways, Service Mesh, gRPC)"
    ],
    "Data Engineering & Big Data": [
        "Apache Kafka / RabbitMQ (Event Streaming & Queues)",
        "Apache Spark / PySpark (Distributed Processing)",
        "ETL Pipelines & Automated Log Ingestion",
        "Pandas, NumPy & Data Wrangling"
    ],
    "Core CS & Systems Engineering": [
        "Data Structures & Algorithms (LeetCode / Problem Solving)",
        "C / C++ / Rust Systems Programming",
        "Object-Oriented Programming (OOP) & SOLID Principles",
        "System Design (Caching with Redis, Load Balancing, Rate Limiting)"
    ],
    "Cybersecurity & QA": [
        "Network Security, OWASP Top 10, JWT Auth & RBAC",
        "Automated Testing (PyTest, Jest, Selenium, Cypress)"
    ]
}
