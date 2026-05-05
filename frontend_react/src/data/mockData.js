export const mockProjects = [
  {
    id: 'p1',
    name: 'E-Commerce Platform',
    createdAt: '2023-10-24T10:00:00Z',
  },
  {
    id: 'p2',
    name: 'FinTech Dashboard',
    createdAt: '2023-10-25T14:30:00Z',
  },
  {
    id: 'p3',
    name: 'Social Media Analytics',
    createdAt: '2023-10-26T09:15:00Z',
  }
];

export const mockChatHistory = {
  p1: [
    { id: 'm1', role: 'user', content: 'What should the architecture be for a high-traffic e-commerce site?' },
    { id: 'm2', role: 'assistant', content: 'I recommend a microservices architecture or a horizontally scalable monolith for high traffic. Caching (Redis) and CDN usage are essential.' },
    { id: 'm3', role: 'user', content: 'What should I choose for the database?' },
    { id: 'm4', role: 'assistant', content: 'PostgreSQL for relational data (orders, cart, users), Elasticsearch for product catalog search (full-text search), and Redis for session and cart ephemerality are a good trio.' }
  ],
  p2: [
    { id: 'm1', role: 'user', content: "We are building a dashboard that will integrate with Banking APIs. What should the security measures be?" },
    { id: 'm2', role: 'assistant', content: 'Security is the number 1 priority in Fintech projects. OAuth 2.0 / OIDC, mTLS (Mutual TLS), database encryption (Data at rest), PCI-DSS compliance, and strict Rate Limiting are required.' }
  ],
  p3: [
    { id: 'm1', role: 'user', content: 'We need to analyze millions of tweets a day.' },
    { id: 'm2', role: 'assistant', content: 'This is a big data problem. You can use Apache Kafka for data streaming, Apache Spark or Flink for data processing, and ClickHouse or BigQuery for analytical queries.' }
  ]
};

export const mockStackRecommendations = {
  p1: {
    frontend: "- React or Next.js\n- Tailwind CSS\n- Redux Toolkit or Zustand for state management\n\nWhy: Next.js SSR (Server Side Rendering) support is excellent for SEO, critical for e-commerce.",
    backend: "- Node.js (Express/NestJS) or Python (FastAPI)\n- GraphQL or REST API\n\nWhy: Lightweight frameworks that are easy to decouple when transitioning to a microservices architecture.",
    database: "- Primary DB: PostgreSQL\n- Cache & Session: Redis\n- Search: Elasticsearch\n\nWhy: ACID compliance is mandatory for e-commerce (payments). Redis increases speed.",
    devops: "- Docker & Kubernetes (K8s)\n- CI/CD: GitHub Actions or GitLab CI\n- Cloud: AWS (EKS, RDS)\n\nWhy: K8s is the industry standard for auto-scaling under high traffic."
  },
  p2: {
    frontend: "- React\n- Material-UI or Ant Design\n- Chart.js or Recharts\n\nWhy: Rich component libraries save time for dashboard interfaces.",
    backend: "- Java (Spring Boot) or C# (.NET Core)\n\nWhy: Most corporate finance firms rely on the Java/.NET ecosystem, security libraries are very mature.",
    database: "- PostgreSQL (or Oracle)\n- For Time Series Data: TimescaleDB\n\nWhy: Strict integrity rules are required for financial transactions.",
    devops: "- On-premise or Private Cloud\n- HashiCorp Vault (Secret management)\n\nWhy: Fintech regulations may restrict data from leaving the country or staying on a public cloud."
  },
  p3: {
    frontend: "- Vue.js or React\n- D3.js (Advanced visualization)\n\nWhy: Render performance is important as there will be a lot of live data streaming.",
    backend: "- Go (Golang) or Rust\n- Apache Kafka (Message Queue)\n\nWhy: Go's concurrency model and low memory footprint provide an advantage when processing millions of data points.",
    database: "- ClickHouse or Apache Druid\n- MongoDB (for metadata)\n\nWhy: OLAP (Online Analytical Processing) systems can perform millisecond analysis on massive datasets.",
    devops: "- AWS EMR or Google Cloud Dataflow\n- Terraform (IaC)\n\nWhy: Managing big data infrastructure is difficult, managed services reduce the workload."
  }
};
