/* ===================================================
   AURORA Beauty Lab — PREMIUM JS
   Слайдер hero, счётчики, маска телефона,
   reveal-анимации, валидация, мобильное меню.
   =================================================== */

document.addEventListener('DOMContentLoaded', () => {

    // ========================================
    // 1. Шапка при скролле
    // ========================================
    const header = document.getElementById('header');
    const onScroll = () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // ========================================
    // 2. Мобильное меню с блэк-дропом
    // ========================================
    const burger = document.getElementById('burger');
    const nav = document.getElementById('nav');

    burger.addEventListener('click', () => {
        burger.classList.toggle('active');
        nav.classList.toggle('active');
        document.body.style.overflow = nav.classList.contains('active') ? 'hidden' : '';
    });

    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            burger.classList.remove('active');
            nav.classList.remove('active');
            document.body.style.overflow = '';
        });
    });

    // ========================================
    // 3. Hero-слайдер (3 фото, автопереключение 6 сек)
    // ========================================
    const slides = document.querySelectorAll('.hero-slide');
    if (slides.length > 1) {
        let currentSlide = 0;
        const showSlide = (idx) => {
            slides.forEach((s, i) => s.classList.toggle('active', i === idx));
        };
        setInterval(() => {
            currentSlide = (currentSlide + 1) % slides.length;
            showSlide(currentSlide);
        }, 6000);
    }

    // ========================================
    // 4. Счётчики цифр при появлении в viewport
    // ========================================
    const counters = document.querySelectorAll('[data-count]');
    const animateCounter = (el) => {
        const target = parseInt(el.dataset.count, 10);
        const duration = 1800;
        const start = performance.now();
        const step = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            el.textContent = Math.floor(target * eased).toLocaleString('ru-RU');
            if (progress < 1) requestAnimationFrame(step);
            else el.textContent = target.toLocaleString('ru-RU');
        };
        requestAnimationFrame(step);
    };

    if (counters.length > 0) {
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    counterObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(c => counterObserver.observe(c));
    }

    // ========================================
    // 5. Reveal-анимации при скролле
    // ========================================
    const revealElements = document.querySelectorAll(
        '.review-card, .stat-item, .pricing-card, .result-item, .faq-item, .cta-form, .cta-content'
    );

    revealElements.forEach((el, i) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(24px)';
        el.style.transition = `opacity 0.8s cubic-bezier(0.22, 1, 0.36, 1) ${i * 0.05}s, transform 0.8s cubic-bezier(0.22, 1, 0.36, 1) ${i * 0.05}s`;
    });

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });

    revealElements.forEach(el => revealObserver.observe(el));

    // ========================================
    // 6. Маска для телефона +7 (___) ___-__-__
    // ========================================
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', (e) => {
            let val = e.target.value.replace(/\D/g, '');
            if (val.startsWith('8')) val = '7' + val.slice(1);
            if (!val.startsWith('7')) val = '7' + val;
            val = val.slice(0, 11);

            let formatted = '+7';
            if (val.length > 1) formatted += ' (' + val.slice(1, 4);
            if (val.length >= 5) formatted += ') ' + val.slice(4, 7);
            if (val.length >= 8) formatted += '-' + val.slice(7, 9);
            if (val.length >= 10) formatted += '-' + val.slice(9, 11);

            e.target.value = formatted;
        });

        phoneInput.addEventListener('focus', (e) => {
            if (!e.target.value) e.target.value = '+7 (';
        });

        phoneInput.addEventListener('blur', (e) => {
            if (e.target.value === '+7 (' || e.target.value === '+7') {
                e.target.value = '';
            }
        });
    }

    // ========================================
    // 7. Минимальная дата для формы (сегодня)
    // ========================================
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.min = today;
    }

    // ========================================
    // 8. Обработка формы с валидацией
    // ========================================
    const form = document.getElementById('ctaForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();

            // Простая валидация
            const name = form.querySelector('#name');
            const phone = form.querySelector('#phone');
            const service = form.querySelector('#service');
            const date = form.querySelector('#date');
            let isValid = true;

            [name, phone, service, date].forEach(input => {
                if (input && !input.value.trim()) {
                    input.classList.add('error');
                    isValid = false;
                } else if (input) {
                    input.classList.remove('error');
                }
            });

            // Проверка телефона по длине цифр
            const phoneDigits = phone.value.replace(/\D/g, '');
            if (phoneDigits.length !== 11) {
                phone.classList.add('error');
                isValid = false;
            }

            if (!isValid) {
                // Убираем подсветку через 2 сек
                setTimeout(() => {
                    [name, phone, service, date].forEach(input => {
                        if (input) input.classList.remove('error');
                    });
                }, 2000);
                return;
            }

            // Имитация отправки (для демо-версии)
            const btn = form.querySelector('button[type="submit"]');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Отправляем заявку...';
            btn.style.opacity = '0.7';

            setTimeout(() => {
                btn.textContent = '✓ Заявка принята! Перезвоним за 15 мин';
                btn.style.background = 'linear-gradient(135deg, #00c853, #6fb5be)';
                btn.style.opacity = '1';
                btn.style.color = '#fff';

                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '';
                    btn.style.color = '';
                    btn.disabled = false;
                    form.reset();
                }, 4000);
            }, 1200);
        });
    }

    // ========================================
    // 9. Плавный скролл с учётом fixed-шапки
    // ========================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#' || targetId.length <= 1) return;
            const target = document.querySelector(targetId);
            if (!target) return;

            e.preventDefault();
            const headerHeight = header.offsetHeight;
            const top = target.getBoundingClientRect().top + window.scrollY - headerHeight - 20;
            window.scrollTo({ top, behavior: 'smooth' });
        });
    });

    // ========================================
    // 10. Скрытие floating-CTA при скролле к форме
    // ========================================
    const floatingCta = document.querySelector('.floating-cta');
    const ctaSection = document.getElementById('cta');
    if (floatingCta && ctaSection) {
        const ctaObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                floatingCta.style.opacity = entry.isIntersecting ? '0' : '1';
                floatingCta.style.pointerEvents = entry.isIntersecting ? 'none' : 'auto';
                floatingCta.style.transform = entry.isIntersecting
                    ? 'translateY(100px)'
                    : 'translateY(0)';
            });
        }, { threshold: 0.2 });
        ctaObserver.observe(ctaSection);
    }

    // ========================================
    // 11. APPLE-STYLE: Parallax для hero-media
    // Фоновое фото двигается медленнее текста (0.4× скорости)
    // ========================================
    try {
    const heroMedia = document.querySelector('.hero-media');
    const heroContent = document.querySelector('.hero-content');
    if (heroMedia && heroContent) {
        let ticking = false;
        const updateParallax = () => {
            const scrolled = window.scrollY;
            if (scrolled < window.innerHeight) {
                heroMedia.style.transform = `translate3d(0, ${scrolled * 0.4}px, 0) scale(${1 + scrolled * 0.0003})`;
                heroContent.style.transform = `translate3d(0, ${scrolled * 0.15}px, 0)`;
                heroContent.style.opacity = `${1 - scrolled / (window.innerHeight * 0.85)}`;
            }
            ticking = false;
        };
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateParallax);
                ticking = true;
            }
        }, { passive: true });
    }
    } catch (e) { console.error('block 11 parallax:', e); }

    // ========================================
    // 12. APPLE-STYLE: Scroll-driven насыщенность hero
    // По мере скролла увеличиваем яркость и контраст
    // ========================================
    try {
    const heroSlides = document.querySelectorAll('.hero-slide');
    if (heroSlides.length > 0) {
        let satTick = false;
        const updateSaturation = () => {
            const scrolled = window.scrollY;
            const ratio = Math.min(scrolled / 600, 1);
            const sat = 100 + ratio * 20;       // 100 → 120
            const con = 100 + ratio * 10;       // 100 → 110
            const bri = 100 - ratio * 15;       // 100 → 85 (затемнение)
            heroSlides.forEach(s => {
                s.style.filter = `saturate(${sat}%) contrast(${con}%) brightness(${bri}%)`;
            });
            satTick = false;
        };
        window.addEventListener('scroll', () => {
            if (!satTick) {
                requestAnimationFrame(updateSaturation);
                satTick = true;
            }
        }, { passive: true });
    }
    } catch (e) { console.error('block 12 saturation:', e); }

    // ========================================
    // 13. APPLE-STYLE: Pinned секция «Команда»
    // Заголовок и подзаголовок фиксируются, карточки листаются
    // Обновление на КАЖДЫЙ scroll (не только на IO threshold),
    // иначе карточки залипают в начальном translateY/scale.
    // ========================================
    try {
    const teamSection = document.querySelector('.team');
    if (teamSection) {
        const teamHeader = teamSection.querySelector('.section-header');
        const teamGrid = teamSection.querySelector('.team-grid');
        const cards = teamGrid ? teamGrid.querySelectorAll('.team-card') : [];
        let teamTicking = false;
        const updateTeam = () => {
            const rect = teamSection.getBoundingClientRect();
            const vh = window.innerHeight;
            if (rect.top < 80 && rect.bottom > vh * 0.3) {
                if (teamHeader) {
                    teamHeader.style.position = 'sticky';
                    teamHeader.style.top = '90px';
                    teamHeader.style.opacity = '1';
                }
                const teamHeight = teamSection.offsetHeight;
                const offset = -rect.top;
                const denom = Math.max(1, teamHeight - vh);
                const progress = Math.max(0, Math.min(offset / denom, 1));
                cards.forEach((card, i) => {
                    const stagger = i * 0.08;
                    const localProgress = Math.max(0, Math.min((progress - stagger) / 0.6, 1));
                    const translateY = (1 - localProgress) * 40;
                    const scale = 0.9 + localProgress * 0.1;
                    card.style.transform = `translateY(${translateY}px) scale(${scale})`;
                    card.style.opacity = 0.4 + localProgress * 0.6;
                });
            } else if (rect.bottom < vh * 0.3) {
                if (teamHeader) teamHeader.style.opacity = '0.3';
            } else {
                if (teamHeader) {
                    teamHeader.style.position = '';
                    teamHeader.style.opacity = '';
                }
            }
            teamTicking = false;
        };
        window.addEventListener('scroll', () => {
            if (!teamTicking) { requestAnimationFrame(updateTeam); teamTicking = true; }
        }, { passive: true });
        updateTeam();
    }
    } catch (e) { console.error('block 13 pinned team:', e); }

    // ========================================
    // 14. APPLE-STYLE: Reveal-каскад для секций
    // Каждый заголовок секции + абзац появляются волной
    // ========================================
    try {
    const sectionHeaders = document.querySelectorAll('.section-header');
    if (sectionHeaders.length > 0) {
        const headerObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const h = entry.target;
                    const tag = h.querySelector('.section-tag');
                    const title = h.querySelector('.section-title');
                    const sub = h.querySelector('.section-subtitle');
                    [tag, title, sub].forEach((el, i) => {
                        if (!el) return;
                        el.style.opacity = '0';
                        el.style.transform = 'translateY(20px)';
                        el.style.transition = `opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1) ${i * 0.12}s, transform 0.7s cubic-bezier(0.22, 1, 0.36, 1) ${i * 0.12}s`;
                        requestAnimationFrame(() => {
                            requestAnimationFrame(() => {
                                el.style.opacity = '1';
                                el.style.transform = 'translateY(0)';
                            });
                        });
                    });
                    headerObserver.unobserve(h);
                }
            });
        }, { threshold: 0.4 });
        sectionHeaders.forEach(h => headerObserver.observe(h));
    }
    } catch (e) { console.error('block 14 reveal cascade:', e); }

    // ========================================
    // 15. APPLE-STYLE: Scroll-tied progress bar в hero
    // Тонкая золотая линия внизу hero растёт по скроллу
    // ========================================
    try {
    const hero = document.querySelector('.hero');
    if (hero) {
        const progressBar = document.createElement('div');
        progressBar.style.cssText = `
            position: absolute; left: 0; bottom: 0; height: 2px;
            background: linear-gradient(90deg, var(--accent-gold), var(--accent-coral));
            transform-origin: 0 50%; transform: scaleX(0); z-index: 4;
            transition: transform 0.05s linear; width: 100%;
        `;
        hero.appendChild(progressBar);
        let pTick = false;
        const updateProgress = () => {
            const heroRect = hero.getBoundingClientRect();
            const heroH = hero.offsetHeight;
            const scrolled = -heroRect.top;
            const progress = Math.max(0, Math.min(scrolled / (heroH - window.innerHeight), 1));
            progressBar.style.transform = `scaleX(${progress})`;
            pTick = false;
        };
        window.addEventListener('scroll', () => {
            if (!pTick) {
                requestAnimationFrame(updateProgress);
                pTick = true;
            }
        }, { passive: true });
    }
    } catch (e) { console.error('block 15 progress bar:', e); }

    // ========================================
    // 16. APPLE-STYLE: Magnetic hover на CTA-кнопках
    // Кнопка слегка «тянется» к курсору
    // ========================================
    try {
    document.querySelectorAll('.btn-primary').forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const r = btn.getBoundingClientRect();
            const x = e.clientX - r.left - r.width / 2;
            const y = e.clientY - r.top - r.height / 2;
            btn.style.transform = `translate(${x * 0.12}px, ${y * 0.18}px)`;
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = '';
        });
    });
    } catch (e) { console.error('block 16 magnetic hover:', e); }

});
