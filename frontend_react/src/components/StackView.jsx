import React from 'react';

const FRONTEND_ITEMS = [
  {
    id: 'ui',
    label: 'UI_Framework',
    desc: 'React or Next.js. Next.js SSR (Server Side Rendering) support is excellent for SEO, which is critical for e-commerce.',
  },
  {
    id: 'styling',
    label: 'Styling',
    desc: 'Fast and modern UI development with Tailwind CSS.',
  },
  {
    id: 'state',
    label: 'State_Management',
    desc: 'Redux Toolkit or Zustand for state management.',
  },
];

const BACKEND_ITEMS = [
  {
    id: 'runtime',
    label: 'Runtime_&_Frameworks',
    desc: "Node.js (Express/NestJS) or Python (FastAPI). Lightweight frameworks that are easy to decouple when transitioning to a microservices architecture.",
  },
  {
    id: 'api',
    label: 'API_Architecture',
    desc: 'Flexible data transmission with GraphQL or REST API architecture.',
  },
  {
    id: 'db',
    label: 'Database_Management',
    desc: 'Scalable database solutions and management systems.',
  },
];

const SUPPORTING_ITEMS = [
  {
    id: 'os',
    label: 'Operating System',
    desc: 'Linux, Windows Server, or cloud-based environments dictate compatibility and performance at the lowest level.',
  },
  {
    id: 'vcs',
    label: 'Version Control',
    desc: 'Git, often paired with GitHub or GitLab, allows teams to track changes and collaborate.',
  },
  {
    id: 'cicd',
    label: 'CI/CD Pipelines',
    desc: 'Jenkins, GitHub Actions, or GitLab CI automate testing and deployment, reducing release bottlenecks.',
  },
  {
    id: 'containers',
    label: 'Containers & Orchestration',
    desc: 'Docker and Kubernetes simplify packaging applications and scaling them across environments.',
  },
  {
    id: 'apis',
    label: 'APIs',
    desc: 'APIs connect the dots, linking frontend and backend, or tying your system into third-party services such as payments, maps, or identity management.',
  },
];

export default function StackView({ project }) {
  const sections = [
    {
      id: 'frontend',
      title: 'A. Frontend (Client-Side)',
      subtitle: 'The part the user sees and interacts with.',
      items: FRONTEND_ITEMS,
    },
    {
      id: 'backend',
      title: 'B. Backend (Server-Side)',
      subtitle: 'The engine room where business logic runs and data is processed.',
      items: BACKEND_ITEMS,
    },
    {
      id: 'supporting',
      title: 'C. Supporting Technologies',
      subtitle: 'Beyond the core layers, a tech stack includes the tools that keep development and deployment running smoothly.',
      items: SUPPORTING_ITEMS,
    },
  ];

  return (
    <div className="view-container stack-view glass">
      <div className="view-header">
        <h2>{project?.name || 'No Project Selected'} - Stack View</h2>
        <p className="subtitle">Recommended technology stack components</p>
      </div>

      <div className="stack-grid">
        {sections.map((section) => (
          <div key={section.id} className="stack-card glass stack-card-full">
            <div className="stack-card-header">
              <h3>{section.title}</h3>
              <p>{section.subtitle}</p>
            </div>
            <div className="stack-card-content supporting-items-grid">
              {section.items.map((item) => (
                <div key={item.id} className="supporting-item">
                  <span className="supporting-item-label">{item.label}</span>
                  <p className="supporting-item-desc">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
