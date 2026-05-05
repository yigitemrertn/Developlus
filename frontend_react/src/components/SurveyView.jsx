import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, Check } from 'lucide-react';

const SURVEY_PARTS = [
  {
    title: 'PART 1: Project Details',
    questions: [
      {
        id: 'projectName',
        text: 'What is the name of your project?',
        type: 'text',
        placeholder: 'Enter project name...'
      }
    ]
  },
  {
    title: 'PART 2: Business Goals & Scale',
    questions: [
      {
        id: 'q1',
        text: 'What is the primary business goal for this project?',
        options: [
          { value: 'A', text: 'Speed to Market: Launch an MVP as fast as possible to test the idea.' },
          { value: 'B', text: 'Reliability: Building a mission-critical system where downtime is not an option.' },
          { value: 'C', text: 'Flexibility: A modular architecture designed for frequent future pivots.' },
          { value: 'D', text: 'Cost-Efficiency: Sustainable growth with minimum infrastructure spending.' }
        ]
      },
      {
        id: 'q2',
        text: 'What is the expected user scale for the next 12 months?',
        options: [
          { value: 'A', text: 'Small/Niche: 0 - 5,000 active users (Standard workloads).' },
          { value: 'B', text: 'Growth Phase: 5,000 - 100,000 active users (Needs horizontal scaling).' },
          { value: 'C', text: 'Massive Scale: 1M+ users (High-concurrency, global traffic).' },
          { value: 'D', text: 'Internal Tool: Fixed user base with predictable load.' }
        ]
      }
    ]
  },
  {
    title: 'PART 3: Team Seniority & Skill Match',
    questions: [
      {
        id: 'q3',
        text: 'What is the overall seniority level of your development team?',
        options: [
          { value: 'A', text: 'Senior: Highly experienced, capable of handling complex architectures and niche technologies.' },
          { value: 'B', text: 'Mid-level: Solid experience; comfortable with industry standards but prefers well-documented tools.' },
          { value: 'C', text: 'Junior: Capable of building standard features; needs established frameworks and clear guidance.' },
          { value: 'D', text: 'Below Junior / Intern: Learning phase; needs "batteries-included" frameworks with high abstraction.' }
        ]
      },
      {
        id: 'q4',
        text: 'How steep is the learning curve you can afford for this project?',
        options: [
          { value: 'A', text: 'Zero Curve: We must use tools that match our current seniority/skill level immediately.' },
          { value: 'B', text: 'Mild Curve: We can afford 1-2 weeks to learn a new, well-documented technology.' },
          { value: 'C', text: 'Steep Curve: We are willing to learn anything (e.g., Rust, Kubernetes) if it benefits the project.' }
        ]
      }
    ]
  },
  {
    title: 'PART 4: Performance, Ecosystem & Maintenance',
    questions: [
      {
        id: 'q5',
        text: 'How do you balance performance with maintainability?',
        options: [
          { value: 'A', text: 'Performance First: We need the highest speed, even if it adds architectural complexity.' },
          { value: 'B', text: 'Maintenance First: We need a clean, simple stack that is easy to support long-term.' },
          { value: 'C', text: 'Balanced: A hybrid approach using industry-standard tools.' }
        ]
      },
      {
        id: 'q6',
        text: 'How important is the community and ecosystem support?',
        options: [
          { value: 'A', text: 'Vital: We need huge communities (StackOverflow, ready-to-use libraries).' },
          { value: 'B', text: 'Moderate: Standard documentation and a stable ecosystem are sufficient.' },
          { value: 'C', text: 'Independent: We can build our own tools or work with niche technologies.' }
        ]
      }
    ]
  },
  {
    title: 'PART 5: Compliance, Security & Budget',
    questions: [
      {
        id: 'q7',
        text: 'Does the project require specific regulatory compliance?',
        options: [
          { value: 'A', text: 'High: Healthcare (HIPAA), Finance (PCI-DSS), or Government-level security.' },
          { value: 'B', text: 'Standard: General user data protection (GDPR/KVKK) is sufficient.' },
          { value: 'C', text: 'Minimal: Public data only, no sensitive user information.' }
        ]
      },
      {
        id: 'q8',
        text: 'What is your infrastructure and development budget?',
        options: [
          { value: 'A', text: 'Bootstrap ($0): Strictly Free-Tier and Open-Source tools.' },
          { value: 'B', text: 'Standard/Growth: Can afford Managed Services (RDS, Vercel Pro, Managed K8s).' },
          { value: 'C', text: 'Enterprise: High budget for premium performance and 24/7 support.' }
        ]
      }
    ]
  },
  {
    title: 'PART 6: Project Specialization',
    questions: [
      {
        id: 'q9',
        text: 'Which advanced features will be central to your application?',
        options: [
          { value: 'A', text: 'AI & Machine Learning: LLMs, Image/Voice models, or Agentic workflows.' },
          { value: 'B', text: 'Real-time Engine: Instant Chat, Live Data Streams, or WebSockets.' },
          { value: 'C', text: 'Data Intensive: Heavy analytics, Big Data processing, or complex reporting.' },
          { value: 'D', text: 'Standard Web: CRUD operations, E-commerce, or Content Management.' }
        ]
      }
    ]
  }
];

export default function SurveyView({ onComplete, existingProject }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState(() => {
    return existingProject ? { projectName: existingProject.name } : {};
  });

  const handleSelect = (questionId, optionValue) => {
    setAnswers(prev => ({ ...prev, [questionId]: optionValue }));
  };

  const handleNext = () => {
    if (currentStep < SURVEY_PARTS.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = () => {
    console.log('Survey Answers:', answers);
    if (onComplete) onComplete(answers);
    alert('Anket tamamlandı! Sonuçlar konsola yazdırıldı.');
  };

  const currentPart = SURVEY_PARTS[currentStep];
  
  // Check if all questions in the current part have been answered
  const isCurrentPartComplete = currentPart.questions.every(q => {
    if (q.type === 'text') return answers[q.id] && answers[q.id].trim().length > 0;
    return answers[q.id];
  });

  const progressPercentage = ((currentStep + 1) / SURVEY_PARTS.length) * 100;

  return (
    <div className="view-container survey-view glass">
      <div className="view-header">
        <h2>{existingProject ? 'Update Project Survey' : 'New Project Assessment'}</h2>
        <p className="subtitle">Let's find the best tech stack for your needs</p>
      </div>

      <div className="survey-progress-container">
        <div className="survey-progress-bar">
          <div className="survey-progress-fill" style={{ width: `${progressPercentage}%` }}></div>
        </div>
        <div className="survey-progress-text">Step {currentStep + 1} of {SURVEY_PARTS.length}</div>
      </div>

      <div className="survey-content">
        <h3 className="survey-part-title">{currentPart.title}</h3>

        {currentPart.questions.map((q) => (
          <div key={q.id} className="survey-question-block">
            <h4 className="survey-question-text">{q.text}</h4>
            
            {q.type === 'text' ? (
              <div className="input-group">
                <input 
                  type="text" 
                  style={{ width: '100%', padding: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', color: '#e2e4f0', fontSize: '16px' }}
                  placeholder={q.placeholder}
                  value={answers[q.id] || ''}
                  onChange={(e) => handleSelect(q.id, e.target.value)}
                />
              </div>
            ) : (
              <div className="survey-options-grid">
                {q.options.map((opt) => (
                  <div 
                    key={opt.value} 
                    className={`survey-option glass ${answers[q.id] === opt.value ? 'selected' : ''}`}
                    onClick={() => handleSelect(q.id, opt.value)}
                  >
                    <div className="survey-option-letter">{opt.value}</div>
                    <div className="survey-option-text">{opt.text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="survey-nav-footer">
        <button 
          className="survey-nav-btn secondary" 
          onClick={handlePrev} 
          disabled={currentStep === 0}
        >
          <ArrowLeft size={18} />
          <span>Previous</span>
        </button>

        {currentStep === SURVEY_PARTS.length - 1 ? (
          <button 
            className="survey-nav-btn primary" 
            onClick={handleSubmit}
            disabled={!isCurrentPartComplete}
          >
            <span>Submit</span>
            <Check size={18} />
          </button>
        ) : (
          <button 
            className="survey-nav-btn primary" 
            onClick={handleNext}
            disabled={!isCurrentPartComplete}
          >
            <span>Next Step</span>
            <ArrowRight size={18} />
          </button>
        )}
      </div>
    </div>
  );
}
