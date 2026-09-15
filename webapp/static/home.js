// import { initTheme } from './theme.js';

// initTheme('themeToggle');

// // --- lightweight starfield, no dependency on three.js for the homepage ---
// const canvas = document.getElementById('hero-canvas');
// const ctx = canvas.getContext('2d');
// let stars = [];
// let dpr = Math.min(window.devicePixelRatio || 1, 2);

// function resize() {
//   const rect = canvas.parentElement.getBoundingClientRect();
//   canvas.width = rect.width * dpr;
//   canvas.height = rect.height * dpr;
//   canvas.style.width = rect.width + 'px';
//   canvas.style.height = rect.height + 'px';
//   ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
//   seedStars(rect.width, rect.height);
// }

// function seedStars(w, h) {
//   const count = Math.round((w * h) / 6000);
//   stars = Array.from({ length: count }, () => ({
//     x: Math.random() * w,
//     y: Math.random() * h,
//     r: Math.random() * 1.3 + 0.2,
//     baseAlpha: Math.random() * 0.6 + 0.2,
//     twinkleSpeed: Math.random() * 0.02 + 0.005,
//     phase: Math.random() * Math.PI * 2,
//   }));
// }

// let t = 0;
// function draw() {
//   const w = canvas.width / dpr, h = canvas.height / dpr;
//   ctx.clearRect(0, 0, w, h);
//   stars.forEach(s => {
//     const alpha = s.baseAlpha + Math.sin(t * s.twinkleSpeed + s.phase) * 0.25;
//     ctx.beginPath();
//     ctx.fillStyle = `rgba(234,241,248,${Math.max(0, alpha)})`;
//     ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
//     ctx.fill();
//   });
//   t++;
//   requestAnimationFrame(draw);
// }

// window.addEventListener('resize', resize);
// resize();
// draw();
import { initTheme } from './theme.js';

initTheme('themeToggle');

// ================================================================
// HERO STARFIELD
// ================================================================

const canvas = document.getElementById('hero-canvas');

if (canvas) {
    const ctx = canvas.getContext('2d');

    let stars = [];
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let t = 0;

    function seedStars(w, h) {
        const count = Math.round((w * h) / 6000);

        stars = Array.from({ length: count }, () => ({
            x: Math.random() * w,
            y: Math.random() * h,
            r: Math.random() * 1.3 + 0.2,
            baseAlpha: Math.random() * 0.6 + 0.2,
            twinkleSpeed: Math.random() * 0.02 + 0.005,
            phase: Math.random() * Math.PI * 2
        }));
    }

    function resize() {
        const rect = canvas.parentElement.getBoundingClientRect();

        dpr = Math.min(window.devicePixelRatio || 1, 2);

        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;

        canvas.style.width = `${rect.width}px`;
        canvas.style.height = `${rect.height}px`;

        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        seedStars(rect.width, rect.height);
    }

    function draw() {
        const w = canvas.width / dpr;
        const h = canvas.height / dpr;

        ctx.clearRect(0, 0, w, h);

        stars.forEach((star) => {
            const alpha =
                star.baseAlpha +
                Math.sin(t * star.twinkleSpeed + star.phase) * 0.25;

            ctx.beginPath();

            ctx.fillStyle =
                `rgba(234,241,248,${Math.max(0, alpha)})`;

            ctx.arc(
                star.x,
                star.y,
                star.r,
                0,
                Math.PI * 2
            );

            ctx.fill();
        });

        t++;
        requestAnimationFrame(draw);
    }

    window.addEventListener('resize', resize);

    resize();
    draw();
}


// ================================================================
// CINT-70 SATELLITE SCROLL ANIMATION
// ================================================================

const satelliteCanvas =
    document.getElementById('satellite-canvas');

if (satelliteCanvas) {

    const ctx = satelliteCanvas.getContext('2d');

    const TOTAL_FRAMES = 192;
    const frames = [];

    let currentFrame = 0;
    let targetFrame = 0;

    let width = 0;
    let height = 0;


    // ------------------------------------------------------------
    // Frame URL
    // ------------------------------------------------------------

    function getFrameURL(index) {
        const frame = String(index).padStart(3, '0');

        return `/static/videos/satellite/frame_${frame}_delay-0.041s.webp`;
    }


    // ------------------------------------------------------------
    // Resize
    // ------------------------------------------------------------

    function resizeCanvas() {

        const rect =
            satelliteCanvas.getBoundingClientRect();

        const dpr =
            Math.min(window.devicePixelRatio || 1, 2);

        width = rect.width;
        height = rect.height;

        satelliteCanvas.width = width * dpr;
        satelliteCanvas.height = height * dpr;

        satelliteCanvas.style.width = `${width}px`;
        satelliteCanvas.style.height = `${height}px`;

        ctx.setTransform(
            dpr,
            0,
            0,
            dpr,
            0,
            0
        );

        drawFrame(Math.round(currentFrame));
    }


    // ------------------------------------------------------------
    // Draw frame
    // ------------------------------------------------------------

    function drawFrame(index) {

        const image = frames[index];

        if (!image || !image.complete || !image.naturalWidth) {
            return;
        }

        ctx.clearRect(
            0,
            0,
            width,
            height
        );

        const imageWidth = image.naturalWidth;
        const imageHeight = image.naturalHeight;

        const scale = Math.min(
            width / imageWidth,
            height / imageHeight
        );

        const drawWidth = imageWidth * scale;
        const drawHeight = imageHeight * scale;

        const x =
            width -
            drawWidth -
            Math.max(20, width * 0.03);

        const y =
            (height - drawHeight) / 2;

        ctx.drawImage(
            image,
            x,
            y,
            drawWidth,
            drawHeight
        );
    }


    // ------------------------------------------------------------
    // Load frames
    // ------------------------------------------------------------

    function loadFrames() {

        console.log(
            'Loading CINT-70 satellite animation...'
        );

        for (let i = 0; i < TOTAL_FRAMES; i+=3) {

            const image = new Image();

            image.onload = () => {

                frames[i] = image;

                if (i === 0) {
                    drawFrame(0);
                }
            };

            image.onerror = () => {

                console.error(
                    `Failed to load satellite frame: ${getFrameURL(i)}`
                );
            };

            image.src = getFrameURL(i);
        }
    }


    // ------------------------------------------------------------
    // Scroll → frame
    // ------------------------------------------------------------

    function updateScroll() {

        const section =
            document.getElementById(
                'satellite-animation'
            );

        if (!section) {
            return;
        }

        const rect =
            section.getBoundingClientRect();

        const scrollRange =
            section.offsetHeight -
            window.innerHeight;

        if (scrollRange <= 0) {
            return;
        }

        let progress =
            -rect.top / scrollRange;

        progress = Math.max(
            0,
            Math.min(1, progress)
        );

        targetFrame =
            progress * (TOTAL_FRAMES - 1);

        const counter =
            document.getElementById(
                'satellite-frame-number'
            );

        if (counter) {
            counter.textContent =
                String(
                    Math.round(targetFrame)
                ).padStart(3, '0');
        }
    }


    // ------------------------------------------------------------
    // Smooth animation
    // ------------------------------------------------------------

    function animationLoop() {

        currentFrame +=
            (targetFrame - currentFrame) * 0.15;

        drawFrame(
            Math.round(currentFrame)
        );

        requestAnimationFrame(animationLoop);
    }


    // ------------------------------------------------------------
    // Events
    // ------------------------------------------------------------

    window.addEventListener(
        'resize',
        resizeCanvas
    );

    window.addEventListener(
        'scroll',
        updateScroll,
        { passive: true }
    );


    // ------------------------------------------------------------
    // Start
    // ------------------------------------------------------------

    resizeCanvas();
    loadFrames();
    updateScroll();
    animationLoop();
}
// ================================================================
// MISSION BRIEF — CONSTRAINT SCAN
// ================================================================

const missionBrief = document.getElementById("brief");

if (missionBrief) {

    const observer = new IntersectionObserver(
        (entries, observer) => {

            entries.forEach((entry) => {

                if (!entry.isIntersecting) {
                    return;
                }

                missionBrief.classList.add("is-visible");

                animateMissionNumbers();

                observer.unobserve(missionBrief);
            });

        },
        {
            threshold: 0.25
        }
    );

    observer.observe(missionBrief);
}


// ================================================================
// TELEMETRY NUMBER ANIMATION
// ================================================================

function animateMissionNumbers() {

    const values =
        document.querySelectorAll(
            "#brief [data-count]"
        );

    values.forEach((element) => {

        const target =
            Number(element.dataset.count);

        const suffix =
            element.dataset.suffix || "";

        const duration = 900;

        const startTime =
            performance.now();

        function update(currentTime) {

            const elapsed =
                currentTime - startTime;

            const progress =
                Math.min(
                    elapsed / duration,
                    1
                );

            // Smooth ease-out
            const eased =
                1 - Math.pow(1 - progress, 3);

            const current =
                Math.round(target * eased);

            element.textContent =
                current + suffix;

            if (progress < 1) {

                requestAnimationFrame(update);

            } else {

                element.textContent =
                    target + suffix;
            }
        }

        requestAnimationFrame(update);
    });
}