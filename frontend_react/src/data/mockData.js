export const mockProjects = [
  {
    id: 'p1',
    name: 'E-Ticaret Platformu',
    createdAt: '2023-10-24T10:00:00Z',
  },
  {
    id: 'p2',
    name: 'FinTech Dashboard',
    createdAt: '2023-10-25T14:30:00Z',
  },
  {
    id: 'p3',
    name: 'Sosyal Medya Analitik',
    createdAt: '2023-10-26T09:15:00Z',
  }
];

export const mockChatHistory = {
  p1: [
    { id: 'm1', role: 'user', content: 'Yüksek trafikli bir e-ticaret sitesi için mimari nasıl olmalı?' },
    { id: 'm2', role: 'assistant', content: 'Yüksek trafik için mikroservis mimarisi veya yatay ölçeklenebilir bir monolit öneririm. Caching (Redis) ve CDN kullanımı şarttır.' },
    { id: 'm3', role: 'user', content: 'Veritabanı olarak ne seçmeliyim?' },
    { id: 'm4', role: 'assistant', content: 'İlişkisel veriler (sipariş, sepet, kullanıcı) için PostgreSQL, ürün kataloğu arama (full-text search) için Elasticsearch, session ve sepet geçiciliği için Redis iyi bir üçlüdür.' }
  ],
  p2: [
    { id: 'm1', role: 'user', content: 'Bankacılık API\'leri ile entegre olacak bir dashboard yapıyoruz. Güvenlik önlemleri neler olmalı?' },
    { id: 'm2', role: 'assistant', content: 'Fintech projelerinde güvenlik 1 numaralı önceliktir. OAuth 2.0 / OIDC, mTLS (Mutual TLS), veritabanı şifreleme (Data at rest), PCI-DSS uyumluluğu ve sıkı Rate Limiting gereklidir.' }
  ],
  p3: [
    { id: 'm1', role: 'user', content: 'Günde milyonlarca tweet analiz etmemiz gerekiyor.' },
    { id: 'm2', role: 'assistant', content: 'Bu bir big data problemi. Veri akışı için Apache Kafka, veri işleme için Apache Spark veya Flink, analitik sorgular için ClickHouse veya BigQuery kullanabilirsiniz.' }
  ]
};

export const mockStackRecommendations = {
  p1: {
    frontend: "- React veya Next.js\n- Tailwind CSS\n- State yönetimi için Redux Toolkit veya Zustand\n\nNeden: Next.js SSR (Server Side Rendering) desteği ile SEO için mükemmeldir, e-ticaret için bu kritiktir.",
    backend: "- Node.js (Express/NestJS) veya Python (FastAPI)\n- GraphQL veya REST API\n\nNeden: Mikroservis mimarisine geçişte parçalanması kolay, hafif framework'ler.",
    database: "- Primary DB: PostgreSQL\n- Cache & Session: Redis\n- Search: Elasticsearch\n\nNeden: ACID uyumluluğu e-ticaret (ödeme) için zorunludur. Redis hızı artırır.",
    devops: "- Docker & Kubernetes (K8s)\n- CI/CD: GitHub Actions veya GitLab CI\n- Cloud: AWS (EKS, RDS)\n\nNeden: Yüksek trafikte otomatik ölçeklenme (auto-scaling) için K8s endüstri standardıdır."
  },
  p2: {
    frontend: "- React\n- Material-UI veya Ant Design\n- Chart.js veya Recharts\n\nNeden: Dashboard arayüzleri için zengin komponent kütüphaneleri hız kazandırır.",
    backend: "- Java (Spring Boot) veya C# (.NET Core)\n\nNeden: Kurumsal finans firmalarının çoğu Java/.NET ekosistemine güvenir, güvenlik kütüphaneleri çok olgundur.",
    database: "- PostgreSQL (veya Oracle)\n- Zaman Serisi Verileri için: TimescaleDB\n\nNeden: Finansal işlemler için katı bütünlük kuralları gerekir.",
    devops: "- On-premise veya Private Cloud\n- HashiCorp Vault (Secret yönetimi)\n\nNeden: Fintech regülasyonları verinin yurt dışına çıkmasını veya public cloud'da durmasını kısıtlayabilir."
  },
  p3: {
    frontend: "- Vue.js veya React\n- D3.js (İleri düzey görselleştirme)\n\nNeden: Çok fazla canlı veri akışı olacağı için render performansı önemlidir.",
    backend: "- Go (Golang) veya Rust\n- Apache Kafka (Message Queue)\n\nNeden: Milyonlarca veriyi işlerken Go'nun concurrency modeli ve düşük bellek tüketimi avantaj sağlar.",
    database: "- ClickHouse veya Apache Druid\n- MongoDB (metadata için)\n\nNeden: OLAP (Online Analytical Processing) sistemleri devasa verilerde milisaniyelik analizler yapabilir.",
    devops: "- AWS EMR veya Google Cloud Dataflow\n- Terraform (IaC)\n\nNeden: Big data altyapısını yönetmek zordur, managed servisler (yönetilen hizmetler) iş yükünü azaltır."
  }
};
