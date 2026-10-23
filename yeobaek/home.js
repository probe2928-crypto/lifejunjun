const track = document.getElementById('heroTrack');
const slides = [...track.querySelectorAll('.hero-slide')];
const dots = [...document.querySelectorAll('[data-slide]')];
let activeSlide = 0;
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
function reflectSlide(index, announce = false) {
  activeSlide = index;
  dots.forEach((dot, i) => {
    dot.classList.toggle('active', i === index);
    if (i === index) dot.setAttribute('aria-current', 'true'); else dot.removeAttribute('aria-current');
  });
  document.getElementById('heroCount').innerHTML = `${String(index + 1).padStart(2, '0')} <span>/ 05</span>`;
  slides.forEach((slide, i) => { slide.inert = i !== index; });
  if (announce) document.getElementById('heroStatus').textContent = slides[index].getAttribute('aria-label');
}
function goTo(index) {
  const next = (index + slides.length) % slides.length;
  // Unset inert before scrolling so controls on the destination are ready immediately.
  slides[next].inert = false;
  track.scrollTo({ left: slides[next].offsetLeft - slides[0].offsetLeft, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
  reflectSlide(next, true);
}
document.getElementById('heroPrev').onclick = () => goTo(activeSlide - 1);
document.getElementById('heroNext').onclick = () => goTo(activeSlide + 1);
dots.forEach(dot => dot.onclick = () => goTo(Number(dot.dataset.slide)));
track.addEventListener('keydown', event => {
  if (event.target !== track) return;
  if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') { event.preventDefault(); goTo(activeSlide + (event.key === 'ArrowRight' ? 1 : -1)); }
});
let pending = false;
track.addEventListener('scroll', () => {
  if (pending) return;
  pending = true;
  requestAnimationFrame(() => {
    const closest = Math.max(0, Math.min(slides.length - 1, Math.round(track.scrollLeft / track.clientWidth)));
    reflectSlide(closest);
    pending = false;
  });
}, { passive: true });
window.addEventListener('resize', () => {
  track.scrollTo({ left: slides[activeSlide].offsetLeft - slides[0].offsetLeft, behavior: 'instant' });
});
document.querySelectorAll('[data-journey]').forEach(button => button.onclick = () => window.openDetail(Number(button.dataset.journey)));
document.querySelectorAll('[data-inquire]').forEach(button => button.onclick = () => window.openInquiry(Number(button.dataset.inquire)));
document.getElementById('heroQuickForm').onsubmit = event => {
  event.preventDefault();
  const name = document.getElementById('quickName').value.trim();
  const message = document.getElementById('quickMessage').value.trim();
  if (name) document.getElementById('name').value = name;
  if (message) document.getElementById('message').value = message;
  window.openInquiry(document.getElementById('quickTrip').value || undefined);
  document.getElementById('email').focus({ preventScroll: true });
};
reflectSlide(0);
