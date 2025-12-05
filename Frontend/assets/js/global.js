// === MOBILE MENU FUNCTIONALITY ===
document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector("nav ul");
  const body = document.body;
  const themeToggle = document.getElementById('theme-toggle');

  function initMobileMenu() {
    if (!menuToggle || !nav) return;

    menuToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleMenu();
    });

    const menuLinks = nav.querySelectorAll('a');
    menuLinks.forEach(link => {
      link.addEventListener('click', () => {
        closeMenu();
      });
    });

    document.addEventListener('click', (e) => {
      if (nav.classList.contains('open') && 
          !nav.contains(e.target) && 
          e.target !== menuToggle) {
        closeMenu();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && nav.classList.contains('open')) {
        closeMenu();
      }
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 900) {
        closeMenu();
      }
    });
  }

  function toggleMenu() {
    if (nav.classList.contains('open')) {
      closeMenu();
    } else {
      openMenu();
    }
  }

  function openMenu() {
    nav.classList.add('open');
    menuToggle.innerHTML = '✕';
    menuToggle.setAttribute('aria-expanded', 'true');
    body.classList.add('menu-open');
    addBackdrop();
  }

  function closeMenu() {
    nav.classList.remove('open');
    menuToggle.innerHTML = '☰';
    menuToggle.setAttribute('aria-expanded', 'false');
    body.classList.remove('menu-open');
    removeBackdrop();
  }

  function addBackdrop() {
    removeBackdrop();
    const backdrop = document.createElement('div');
    backdrop.className = 'menu-backdrop';
    backdrop.addEventListener('click', closeMenu);
    document.body.appendChild(backdrop);
  }

  function removeBackdrop() {
    const backdrop = document.querySelector('.menu-backdrop');
    if (backdrop) {
      backdrop.remove();
    }
  }

  initMobileMenu();

  function initTheme() {
    try {
      const saved = localStorage.getItem('theme');
      if (saved === 'dark') body.classList.add('dark');
    } catch {}
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark');
        try {
          localStorage.setItem('theme', body.classList.contains('dark') ? 'dark' : 'light');
        } catch {}
        themeToggle.textContent = body.classList.contains('dark') ? '☀️' : '🌙';
      });
      themeToggle.textContent = body.classList.contains('dark') ? '☀️' : '🌙';
    }
  }
  initTheme();

  const backTop = document.getElementById('back-to-top');
  function onScroll(){
    if (!backTop) return;
    if (window.scrollY > 300) backTop.classList.add('show'); else backTop.classList.remove('show');
  }
  function onTop(){ window.scrollTo({ top: 0, behavior: 'smooth' }); }
  window.addEventListener('scroll', onScroll);
  backTop && backTop.addEventListener('click', onTop);
  onScroll();
});