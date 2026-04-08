// Kategori verileri ve yardımcı fonksiyonlar

export const categories = [
  {
    id: 'frontend', name: 'Frontend', icon: 'Monitor', cls: 'cat-frontend',
    techs: ['React + Vite', 'Next.js', 'Vue 3 + Nuxt', 'Svelte', 'Angular'],
    descs: [
      'Modern component-based SPA mimarisi',
      'SSR ve ISR ile yüksek performans',
      'Reactive framework ile hızlı geliştirme',
      'Minimal bundle size ile hız',
      'Enterprise-grade uygulama geliştirme'
    ]
  },
  {
    id: 'backend', name: 'Backend', icon: 'Server', cls: 'cat-backend',
    techs: ['Node.js + Express', 'NestJS', 'Django', 'FastAPI', 'Go Fiber'],
    descs: [
      'Hızlı ve esnek REST API geliştirme',
      'TypeScript ile yapılandırılmış backend',
      'Python ekosistemi ile güçlü backend',
      'Yüksek performanslı async API',
      'Düşük gecikme süresi ile yüksek performans'
    ]
  },
  {
    id: 'database', name: 'Veritabanı', icon: 'Database', cls: 'cat-database',
    techs: ['PostgreSQL', 'MongoDB', 'Supabase', 'PlanetScale', 'Redis'],
    descs: [
      'Güvenilir ilişkisel veritabanı',
      'Esnek NoSQL doküman veritabanı',
      'Açık kaynak Firebase alternatifi',
      'Serverless MySQL çözümü',
      'In-memory cache ve veri deposu'
    ]
  },
  {
    id: 'arch', name: 'Mimari', icon: 'GitBranch', cls: 'cat-arch',
    techs: ['Microservices', 'Monolith', 'Serverless', 'Event-Driven', 'Modular Monolith'],
    descs: [
      'Ölçeklenebilir dağıtık sistem',
      'Hızlı başlangıç için tek yapı',
      'Altyapı yönetimi gerektirmeyen mimari',
      'Asenkron olay tabanlı iletişim',
      'Monolith avantajları ile modüler yapı'
    ]
  },
  {
    id: 'auth', name: 'Auth', icon: 'Shield', cls: 'cat-auth',
    techs: ['NextAuth.js', 'Clerk', 'Supabase Auth', 'Firebase Auth', 'Keycloak'],
    descs: [
      'Kolay entegre authentication',
      'Modern kullanıcı yönetimi',
      'Tam entegre auth çözümü',
      'Google ve sosyal login desteği',
      'Enterprise IAM çözümü'
    ]
  },
  {
    id: 'deploy', name: 'Deployment', icon: 'Cloud', cls: 'cat-deploy',
    techs: ['Vercel', 'AWS', 'Docker + K8s', 'Railway', 'Fly.io'],
    descs: [
      'Frontend için optimize edge deploy',
      'Kapsamlı bulut altyapısı',
      'Container tabanlı orkestrasyon',
      'Kolay backend deployment',
      'Global edge deployment'
    ]
  },
  {
    id: 'cicd', name: 'CI/CD', icon: 'RefreshCw', cls: 'cat-cicd',
    techs: ['GitHub Actions', 'GitLab CI', 'Jenkins', 'CircleCI', 'ArgoCD'],
    descs: [
      'GitHub entegreli otomasyon',
      'Tam entegre DevOps pipeline',
      'Özelleştirilebilir build pipeline',
      'Hızlı ve güvenilir CI çözümü',
      'GitOps ile Kubernetes deploy'
    ]
  },
  {
    id: 'test', name: 'Test', icon: 'CheckCircle', cls: 'cat-test',
    techs: ['Vitest', 'Playwright', 'Jest', 'Cypress', 'Testing Library'],
    descs: [
      'Hızlı unit test framework',
      'End-to-end cross-browser test',
      'JavaScript test standartı',
      'Modern E2E test aracı',
      'Component test odaklı yaklaşım'
    ]
  },
  {
    id: 'security', name: 'Güvenlik', icon: 'Lock', cls: 'cat-security',
    techs: ['Helmet.js', 'OWASP ZAP', 'Snyk', 'Vault', 'Rate Limiting'],
    descs: [
      'HTTP header güvenliği',
      'Otomatik güvenlik taraması',
      'Bağımlılık güvenlik analizi',
      'Secret yönetimi',
      'API kötüye kullanım koruması'
    ]
  },
  {
    id: 'api', name: 'API Tasarımı', icon: 'Globe', cls: 'cat-api',
    techs: ['REST + OpenAPI', 'GraphQL', 'tRPC', 'gRPC', 'WebSocket'],
    descs: [
      'Standart REST API ile dokümantasyon',
      'Esnek sorgu tabanlı API',
      'End-to-end type-safe API',
      'Yüksek performanslı RPC',
      'Gerçek zamanlı çift yönlü iletişim'
    ]
  }
];

export function generateMockResults(input) {
  const lower = input.toLowerCase();
  return categories.map(cat => {
    let idx = Math.floor(Math.random() * cat.techs.length);
    if (cat.id === 'frontend') {
      if (lower.includes('mobil')) idx = 3;
      else if (lower.includes('e-ticaret') || lower.includes('ecommerce')) idx = 1;
    }
    if (cat.id === 'backend') {
      if (lower.includes('python')) idx = 2;
      else if (lower.includes('hız') || lower.includes('performans')) idx = 4;
    }
    if (cat.id === 'database') {
      if (lower.includes('gerçek zamanlı') || lower.includes('realtime')) idx = 4;
      else if (lower.includes('ilişkisel')) idx = 0;
    }
    if (cat.id === 'arch') {
      if (lower.includes('büyük') || lower.includes('ölçek')) idx = 0;
      else if (lower.includes('basit') || lower.includes('mvp')) idx = 1;
    }
    return {
      category: cat.name,
      icon: cat.icon,
      cls: cat.cls,
      tech: cat.techs[idx],
      desc: cat.descs[idx]
    };
  });
}
