#!/bin/bash

# Golden Dataset Ingestion - 20 Documents
# This script ingests 20 diverse documents for testing the RAG system

curl -X POST "http://localhost:8000/agent/ingest/json" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Circuit breakers are safety devices that automatically interrupt electrical current flow when an overload or short circuit is detected. They protect electrical circuits and equipment from damage by preventing excessive current flow.",
      
      "The A1 service is a critical component of the telecommunications infrastructure. It handles authentication, authorization, and access control for network resources. A1 uses OAuth 2.0 protocol for secure token-based authentication.",
      
      "SIM provisioning is the process of activating and configuring a SIM card for use on a mobile network. The provisioning system triggers retry mechanisms when initial activation fails, using exponential backoff to prevent system overload.",
      
      "Circuit breaker pattern protects A1 service from cascading failures. When A1 returns 521 error storms, the circuit breaker opens and returns 429 Too Many Requests to prevent further load on the failing service.",
      
      "Billing systems use BSS (Business Support Systems) pipeline to process subscription updates. The pipeline handles plan changes, payment processing, and account modifications in a transactional manner.",
      
      "API rate limiting prevents abuse and ensures fair resource allocation. Rate limits are enforced using token bucket algorithm, allowing burst traffic while maintaining average rate constraints.",
      
      "Database connection pooling improves application performance by reusing database connections. Connection pools maintain a set of pre-established connections, reducing connection overhead and latency.",
      
      "Microservices architecture decomposes applications into small, independent services. Each service has its own database and communicates via APIs, enabling independent deployment and scaling.",
      
      "Load balancing distributes incoming network traffic across multiple servers to ensure high availability and reliability. Common algorithms include round-robin, least connections, and weighted distribution.",
      
      "Caching strategies improve application performance by storing frequently accessed data in fast storage. Redis and Memcached are popular in-memory caching solutions that reduce database load.",
      
      "Message queues enable asynchronous communication between services. RabbitMQ and Apache Kafka are popular message brokers that support pub-sub patterns and reliable message delivery.",
      
      "Container orchestration platforms like Kubernetes manage containerized applications at scale. They handle deployment, scaling, load balancing, and self-healing of container clusters.",
      
      "CI/CD pipelines automate software testing and deployment processes. Continuous Integration runs automated tests on code commits, while Continuous Deployment automatically releases tested code to production.",
      
      "Monitoring and observability tools track application health and performance. Metrics, logs, and traces provide insights into system behavior, enabling proactive issue detection and resolution.",
      
      "Security best practices include encryption at rest and in transit, regular security audits, and implementing least privilege access controls. OAuth 2.0 and JWT tokens provide secure authentication mechanisms.",
      
      "Data replication ensures high availability by maintaining copies of data across multiple locations. Master-slave and master-master replication patterns provide redundancy and enable disaster recovery.",
      
      "Event-driven architecture uses events to trigger and communicate between services. Event sourcing stores all changes as a sequence of events, enabling complete audit trails and time-travel debugging.",
      
      "GraphQL provides a flexible query language for APIs, allowing clients to request exactly the data they need. It reduces over-fetching and under-fetching compared to traditional REST APIs.",
      
      "Serverless computing abstracts server management, allowing developers to focus on code. Functions are executed on-demand, scaling automatically with request volume and charging only for actual usage.",
      
      "Distributed tracing tracks requests across multiple services in a microservices architecture. Tools like Jaeger and Zipkin visualize request flows, helping identify performance bottlenecks and failures."
    ],
    "metadatas": [
      {"topic": "circuit_breaker", "category": "infrastructure", "doc_id": "doc_001"},
      {"topic": "authentication", "category": "security", "doc_id": "doc_002"},
      {"topic": "provisioning", "category": "telecom", "doc_id": "doc_003"},
      {"topic": "circuit_breaker", "category": "resilience", "doc_id": "doc_004"},
      {"topic": "billing", "category": "business", "doc_id": "doc_005"},
      {"topic": "rate_limiting", "category": "api", "doc_id": "doc_006"},
      {"topic": "database", "category": "performance", "doc_id": "doc_007"},
      {"topic": "architecture", "category": "design", "doc_id": "doc_008"},
      {"topic": "load_balancing", "category": "infrastructure", "doc_id": "doc_009"},
      {"topic": "caching", "category": "performance", "doc_id": "doc_010"},
      {"topic": "messaging", "category": "integration", "doc_id": "doc_011"},
      {"topic": "orchestration", "category": "devops", "doc_id": "doc_012"},
      {"topic": "cicd", "category": "devops", "doc_id": "doc_013"},
      {"topic": "monitoring", "category": "observability", "doc_id": "doc_014"},
      {"topic": "security", "category": "best_practices", "doc_id": "doc_015"},
      {"topic": "replication", "category": "database", "doc_id": "doc_016"},
      {"topic": "event_driven", "category": "architecture", "doc_id": "doc_017"},
      {"topic": "graphql", "category": "api", "doc_id": "doc_018"},
      {"topic": "serverless", "category": "cloud", "doc_id": "doc_019"},
      {"topic": "tracing", "category": "observability", "doc_id": "doc_020"}
    ]
  }'

echo ""
echo "✅ Golden dataset ingestion complete! 20 documents ingested."

