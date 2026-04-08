export default function HowItWorks() {
  const steps = [
    {
      num: '01',
      title: 'Projeni Yaz',
      desc: 'Geliştirmek istediğin yazılım projesini birkaç cümleyle açıkla.'
    },
    {
      num: '02',
      title: 'Analizi Başlat',
      desc: 'Yapay zeka motoru proje fikrini detaylı şekilde analiz etsin.'
    },
    {
      num: '03',
      title: 'Önerileri Al',
      desc: '10 farklı kategori altında en uygun teknoloji önerilerini keşfet.'
    }
  ];

  return (
    <section className="how-section" id="how">
      <div className="section-inner">
        <h2 className="section-title">Nasıl Çalışır?</h2>
        <p className="section-subtitle">3 basit adımda proje teknoloji haritanı oluştur</p>
        <div className="steps-grid">
          {steps.map((step, i) => (
            <div key={step.num} className={`glass step-card fade-in stagger-${i + 1}`}>
              <span className="step-num">{step.num}</span>
              <h3>{step.title}</h3>
              <p>{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
