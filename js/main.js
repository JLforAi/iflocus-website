// iFLocus Website - Main JavaScript

// ===== NAVBAR =====
// Must run after DOMContentLoaded so components.js has already injected the header
document.addEventListener('DOMContentLoaded', function () {
  const hamburger = document.getElementById('navHamburger');
  const navMenu = document.getElementById('navMenu');

  if (hamburger && navMenu) {
    hamburger.addEventListener('click', function () {
      navMenu.classList.toggle('open');
      hamburger.classList.toggle('active');
    });
  }

  // Mobile dropdown toggle
  document.querySelectorAll('.has-dropdown > a').forEach(function (link) {
    link.addEventListener('click', function (e) {
      if (window.innerWidth <= 768) {
        e.preventDefault();
        this.parentElement.classList.toggle('open');
      }
    });
  });

  // Active page highlight
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-menu a').forEach(function (a) {
    if (a.getAttribute('href') === currentPath) {
      a.closest('li').classList.add('active');
    }
  });

  // Close menu on outside click
  document.addEventListener('click', function (e) {
    if (navMenu && hamburger &&
        !navMenu.contains(e.target) && !hamburger.contains(e.target)) {
      navMenu.classList.remove('open');
    }
  });
});

// ===== HERO SLIDER =====
(function () {
  const slider = document.querySelector('.hero-slider');
  if (!slider) return;

  const slides = slider.querySelectorAll('.slide');
  const dotsContainer = slider.querySelector('.slider-controls');
  let current = 0;
  let timer;

  function goTo(n) {
    slides[current].classList.remove('active');
    if (dotsContainer) {
      dotsContainer.querySelectorAll('.slider-dot')[current].classList.remove('active');
    }
    current = (n + slides.length) % slides.length;
    slides[current].classList.add('active');
    if (dotsContainer) {
      dotsContainer.querySelectorAll('.slider-dot')[current].classList.add('active');
    }
  }

  function autoPlay() {
    timer = setInterval(function () { goTo(current + 1); }, 5000);
  }

  function resetTimer() {
    clearInterval(timer);
    autoPlay();
  }

  // Build dots
  if (dotsContainer && slides.length > 1) {
    slides.forEach(function (_, i) {
      const dot = document.createElement('button');
      dot.className = 'slider-dot' + (i === 0 ? ' active' : '');
      dot.addEventListener('click', function () { goTo(i); resetTimer(); });
      dotsContainer.appendChild(dot);
    });
  }

  // Arrow buttons
  const prev = slider.querySelector('.slider-arrow.prev');
  const next = slider.querySelector('.slider-arrow.next');
  if (prev) prev.addEventListener('click', function () { goTo(current - 1); resetTimer(); });
  if (next) next.addEventListener('click', function () { goTo(current + 1); resetTimer(); });

  if (slides.length > 0) {
    slides[0].classList.add('active');
    if (slides.length > 1) autoPlay();
  }
})();

// ===== BACK TO TOP =====
(function () {
  const btn = document.getElementById('backToTop');
  if (!btn) return;

  window.addEventListener('scroll', function () {
    btn.classList.toggle('show', window.scrollY > 400);
  });

  btn.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

// ===== SCROLL ANIMATIONS =====
(function () {
  if (!window.IntersectionObserver) return;

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });

  document.querySelectorAll('.card, .feature-item, .pricing-card, .news-card, .stat-item').forEach(function (el) {
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    observer.observe(el);
  });
})();

// ===== CONTACT FORM =====
(function () {
  const form = document.getElementById('contactForm');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const original = btn.textContent;
    btn.textContent = '已送出，感謝您的來信！';
    btn.disabled = true;
    btn.style.background = '#28a745';
    setTimeout(function () {
      btn.textContent = original;
      btn.disabled = false;
      btn.style.background = '';
      form.reset();
    }, 4000);
  });
})();

// ===== STICKY HEADER SHADOW =====
(function () {
  const header = document.querySelector('.site-header');
  if (!header) return;
  window.addEventListener('scroll', function () {
    header.style.boxShadow = window.scrollY > 10
      ? '0 4px 20px rgba(0,0,0,0.12)'
      : '0 2px 12px rgba(0,0,0,0.08)';
  });
})();
