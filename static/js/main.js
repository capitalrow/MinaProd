document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initDropdowns();
  initMobileMenu();
  initAlerts();
});

function initThemeToggle() {
  const themeToggle = document.getElementById('theme-toggle');
  if (!themeToggle) return;

  const html = document.documentElement;
  const darkIcon = themeToggle.querySelector('.theme-icon-dark');
  const lightIcon = themeToggle.querySelector('.theme-icon-light');

  const savedTheme = localStorage.getItem('theme') || 'dark';
  html.setAttribute('data-theme', savedTheme);
  updateThemeIcons(savedTheme, darkIcon, lightIcon);

  themeToggle.addEventListener('click', () => {
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcons(newTheme, darkIcon, lightIcon);
  });
}

function updateThemeIcons(theme, darkIcon, lightIcon) {
  if (theme === 'dark') {
    darkIcon?.classList.remove('hidden');
    lightIcon?.classList.add('hidden');
  } else {
    darkIcon?.classList.add('hidden');
    lightIcon?.classList.remove('hidden');
  }
}

function initDropdowns() {
  document.querySelectorAll('.dropdown').forEach(dropdown => {
    const button = dropdown.querySelector('[aria-haspopup="true"]');
    const menu = dropdown.querySelector('.dropdown-menu');
    
    if (!button || !menu) return;

    button.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = menu.classList.contains('active');
      
      document.querySelectorAll('.dropdown-menu').forEach(m => m.classList.remove('active'));
      
      if (!isOpen) {
        menu.classList.add('active');
        button.setAttribute('aria-expanded', 'true');
      } else {
        menu.classList.remove('active');
        button.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('click', (e) => {
      if (!dropdown.contains(e.target)) {
        menu.classList.remove('active');
        button.setAttribute('aria-expanded', 'false');
      }
    });

    menu.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        menu.classList.remove('active');
        button.setAttribute('aria-expanded', 'false');
        button.focus();
      }
    });
  });
}

function initMobileMenu() {
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  const navbarMenu = document.querySelector('.navbar-menu');
  
  if (!mobileMenuButton || !navbarMenu) return;

  mobileMenuButton.addEventListener('click', () => {
    const isExpanded = mobileMenuButton.getAttribute('aria-expanded') === 'true';
    
    if (isExpanded) {
      navbarMenu.style.display = 'none';
      mobileMenuButton.setAttribute('aria-expanded', 'false');
    } else {
      navbarMenu.style.display = 'flex';
      navbarMenu.style.position = 'absolute';
      navbarMenu.style.top = 'var(--header-height)';
      navbarMenu.style.left = '0';
      navbarMenu.style.right = '0';
      navbarMenu.style.flexDirection = 'column';
      navbarMenu.style.backgroundColor = 'var(--color-surface)';
      navbarMenu.style.padding = 'var(--space-4)';
      navbarMenu.style.borderBottom = '1px solid var(--color-border)';
      mobileMenuButton.setAttribute('aria-expanded', 'true');
    }
  });
}

function initAlerts() {
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.position = 'fixed';
  toast.style.top = 'var(--space-8)';
  toast.style.right = 'var(--space-8)';
  toast.style.zIndex = 'var(--z-tooltip)';
  toast.style.minWidth = '300px';
  toast.innerHTML = `<span>${message}</span>`;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

window.showToast = showToast;
