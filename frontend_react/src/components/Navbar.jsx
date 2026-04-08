export default function Navbar({ onHomeClick }) {
  return (
    <nav>
      <div className="nav-inner">
        <div className="logo-text">⟨/⟩ developlus</div>
        <ul className="nav-links">
          <li><a href="#hero" onClick={onHomeClick}>Ana Sayfa</a></li>
          <li><a href="#how">Nasıl Çalışır</a></li>
          <li><a href="#features">Özellikler</a></li>
        </ul>
      </div>
    </nav>
  );
}
