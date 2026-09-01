import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import altair as alt
import hashlib
import secrets
import db as tradingdb


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="PortfolioLab",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM STYLING
# =========================================================

st.session_state.setdefault("theme", "dark")


def get_theme_colors():
    if st.session_state["theme"] == "light":
        return {
            "bg": "#F7F8FA",
            "text": "#1A1D23",
            "grid_dot": "rgba(0,0,0,0.04)",
            "grid_line_base_js": "{ r: 0, g: 0, b: 0, a: 0.07 }",
            "aurora_base": (
                "repeating-linear-gradient(100deg, #fff 0%, #fff 7%, "
                "transparent 10%, transparent 12%, #fff 16%)"
            ),
            "aurora_invert": "1",
        }
    return {
        "bg": "#161618",
        "text": "#FAFAFA",
        "grid_dot": "rgba(255,255,255,0.035)",
        "grid_line_base_js": "{ r: 255, g: 255, b: 255, a: 0.09 }",
        "aurora_base": (
            "repeating-linear-gradient(100deg, #000 0%, #000 7%, "
            "transparent 10%, transparent 12%, #000 16%)"
        ),
        "aurora_invert": "0",
    }


AURORA_COLOR_GRADIENT = (
    "repeating-linear-gradient(100deg, #3b82f6 10%, #a5b4fc 15%, "
    "#93c5fd 20%, #ddd6fe 25%, #60a5fa 30%)"
)

KINETIC_GRID_TEMPLATE = r"""
<style>
html, body {
    background: transparent !important;
    margin: 0;
    overflow: hidden;
}
</style>
<canvas id="kinetic-grid-canvas-local"></canvas>
<script>
(function () {
    var CELL_SIZE = 55;
    var INFLUENCE_RADIUS = 320;
    var MAX_WARP = 22;
    var DOT_SPACING = 28;
    var LERP_SPEED = 0.12;
    var LINE_BASE = __LINE_BASE__;
    var NODE_BASE_RADIUS = 1.8;
    var NODE_ACTIVE_RADIUS = 3.2;
    var DOT_COLOR = '__DOT_COLOR__';

    var theme = {
        lineActive: { r: 74, g: 158, b: 255, a: 0.9 },
        nodeActive: { r: 74, g: 158, b: 255, a: 1.0 },
        glow: '74,158,255',
        ripple: '100,180,255'
    };

    function lerpN(a, b, t) { return a + (b - a) * t; }
    function lerpColor(base, active, t) {
        var r = Math.round(lerpN(base.r, active.r, t));
        var g = Math.round(lerpN(base.g, active.g, t));
        var b = Math.round(lerpN(base.b, active.b, t));
        var a = lerpN(base.a, active.a, t);
        return 'rgba(' + r + ',' + g + ',' + b + ',' + a.toFixed(3) + ')';
    }

    // ---- Try to reach the real top-level page for genuine cursor tracking.
    // Falls back to a self-contained ambient animation if the browser blocks it.
    var win = null, doc = null, canvas = null, REAL_CURSOR = false;

    try {
        var testWin = window.parent;
        var testDoc = testWin.document;
        var probe = testDoc.body.nodeName;  // throws if cross-origin blocked

        if (!testWin.__kineticGridInjected) {
            testWin.__kineticGridInjected = true;
            win = testWin;
            doc = testDoc;

            canvas = doc.createElement('canvas');
            canvas.id = 'kinetic-grid-canvas';
            canvas.style.position = 'fixed';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100vw';
            canvas.style.height = '100vh';
            canvas.style.zIndex = '0';
            canvas.style.pointerEvents = 'none';
            doc.body.insertBefore(canvas, doc.body.firstChild);

            REAL_CURSOR = true;
        }
    } catch (err) {
        REAL_CURSOR = false;
    }

    if (!REAL_CURSOR) {
        win = window;
        doc = document;
        canvas = doc.getElementById('kinetic-grid-canvas-local');
    }

    if (!canvas) { return; }
    var ctx = canvas.getContext('2d');

    var mouse = { x: -9999, y: -9999 };
    var targetMouse = { x: -9999, y: -9999 };
    var ripples = [];
    var size = { w: 0, h: 0 };
    var startTime = performance.now();
    var nextAutoRipple = 2000;

    function setSize() {
        size.w = win.innerWidth;
        size.h = win.innerHeight;
        canvas.width = size.w;
        canvas.height = size.h;
    }
    setSize();
    win.addEventListener('resize', setSize);

    if (REAL_CURSOR) {
        win.addEventListener('mousemove', function (e) {
            targetMouse.x = e.clientX;
            targetMouse.y = e.clientY;
        });
        win.addEventListener('click', function (e) {
            ripples.push({ x: e.clientX, y: e.clientY, radius: 0, opacity: 1, born: performance.now() });
        });
    }

    function getWarpedPoint(gx, gy, col, row, cols, rows) {
        var edgeMargin = 1.5;
        var colPin = Math.min(col / edgeMargin, (cols - 1 - col) / edgeMargin, 1);
        var rowPin = Math.min(row / edgeMargin, (rows - 1 - row) / edgeMargin, 1);
        var pinFactor = colPin * colPin * rowPin * rowPin;

        var dx = gx - mouse.x;
        var dy = gy - mouse.y;
        var dist = Math.sqrt(dx * dx + dy * dy);
        var proximity = Math.max(0, 1 - dist / INFLUENCE_RADIUS) * pinFactor;

        var rx = 0, ry = 0;
        for (var i = 0; i < ripples.length; i++) {
            var r = ripples[i];
            var rdx = gx - r.x;
            var rdy = gy - r.y;
            var rdist = Math.sqrt(rdx * rdx + rdy * rdy);
            var waveWidth = 55;
            var diff = rdist - r.radius;
            if (Math.abs(diff) < waveWidth) {
                var strength = (1 - Math.abs(diff) / waveWidth) * r.opacity * 18 * pinFactor;
                var angle = Math.atan2(rdy, rdx);
                var sign = diff < 0 ? -1 : 1;
                rx += Math.cos(angle) * strength * sign * -1;
                ry += Math.sin(angle) * strength * sign * -1;
            }
        }

        if (dist < INFLUENCE_RADIUS && dist > 0 && pinFactor > 0) {
            var t = dist / INFLUENCE_RADIUS;
            var eased = t < 0.01 ? 0 : (1 - t) * (1 - t) * Math.min(1, dist / 60);
            var warpAmt = eased * MAX_WARP * pinFactor;
            var angle2 = Math.atan2(dy, dx);
            return {
                pt: { x: gx - Math.cos(angle2) * warpAmt + rx, y: gy - Math.sin(angle2) * warpAmt + ry },
                proximity: proximity
            };
        }
        return { pt: { x: gx + rx, y: gy + ry }, proximity: proximity };
    }

    function draw(now) {
        var W = size.w, H = size.h;
        ctx.clearRect(0, 0, W, H);

        ctx.fillStyle = DOT_COLOR;
        for (var x = DOT_SPACING / 2; x < W; x += DOT_SPACING) {
            for (var y = DOT_SPACING / 2; y < H; y += DOT_SPACING) {
                ctx.beginPath();
                ctx.arc(x, y, 0.7, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        if (REAL_CURSOR) {
            mouse.x = lerpN(mouse.x, targetMouse.x, LERP_SPEED);
            mouse.y = lerpN(mouse.y, targetMouse.y, LERP_SPEED);
        } else {
            var elapsed = (now - startTime) / 1000;
            mouse.x = W / 2 + Math.sin(elapsed * 0.25) * (W * 0.35);
            mouse.y = H / 2 + Math.sin(elapsed * 0.4) * (H * 0.3);

            if (now > nextAutoRipple) {
                ripples.push({ x: mouse.x, y: mouse.y, radius: 0, opacity: 1, born: now });
                nextAutoRipple = now + 3200 + Math.random() * 1800;
            }
        }

        for (var i = ripples.length - 1; i >= 0; i--) {
            var r = ripples[i];
            var age = (now - r.born) / 1000;
            r.radius = Math.max(0, age * 400);
            r.opacity = Math.max(0, 1 - age * 1.2);
            if (r.opacity <= 0) ripples.splice(i, 1);
        }

        var cols = Math.max(2, Math.ceil(W / CELL_SIZE)) + 1;
        var rows = Math.max(2, Math.ceil(H / CELL_SIZE)) + 1;
        var cellW = W / (cols - 1);
        var cellH = H / (rows - 1);

        var pts = [];
        var prox = [];
        for (var row = 0; row < rows; row++) {
            pts[row] = [];
            prox[row] = [];
            for (var col = 0; col < cols; col++) {
                var res = getWarpedPoint(col * cellW, row * cellH, col, row, cols, rows);
                pts[row][col] = res.pt;
                prox[row][col] = res.proximity;
            }
        }

        function drawSeg(p1, p2, pr1, pr2) {
            var avg = (pr1 + pr2) / 2;
            var t = avg * avg * (3 - 2 * avg);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = lerpColor(LINE_BASE, theme.lineActive, t);
            ctx.lineWidth = lerpN(0.8, 1.5, t);
            ctx.stroke();
        }

        ctx.lineCap = 'butt';
        for (var row = 0; row < rows; row++)
            for (var col = 0; col < cols - 1; col++)
                drawSeg(pts[row][col], pts[row][col + 1], prox[row][col], prox[row][col + 1]);
        for (var col = 0; col < cols; col++)
            for (var row = 0; row < rows - 1; row++)
                drawSeg(pts[row][col], pts[row + 1][col], prox[row][col], prox[row + 1][col]);

        for (var row = 0; row < rows; row++) {
            for (var col = 0; col < cols; col++) {
                var p = pts[row][col];
                var pr = prox[row][col];
                var t = pr * pr * (3 - 2 * pr);
                var rad = lerpN(NODE_BASE_RADIUS, NODE_ACTIVE_RADIUS, t);

                if (t > 0.3) {
                    var glowR = rad + lerpN(0, 6, (t - 0.3) / 0.7);
                    var grd = ctx.createRadialGradient(p.x, p.y, rad * 0.5, p.x, p.y, glowR);
                    grd.addColorStop(0, 'rgba(' + theme.glow + ',' + (t * 0.3).toFixed(3) + ')');
                    grd.addColorStop(1, 'rgba(' + theme.glow + ',0)');
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, glowR, 0, Math.PI * 2);
                    ctx.fillStyle = grd;
                    ctx.fill();
                }

                ctx.beginPath();
                ctx.arc(p.x, p.y, rad, 0, Math.PI * 2);
                ctx.fillStyle = lerpColor({ r: 255, g: 255, b: 255, a: 0.14 }, theme.nodeActive, t);
                ctx.fill();
            }
        }

        for (var i2 = 0; i2 < ripples.length; i2++) {
            var rp = ripples[i2];
            var safeRadius = Math.max(0, rp.radius);
            ctx.beginPath();
            ctx.arc(rp.x, rp.y, safeRadius, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(' + theme.ripple + ',' + (rp.opacity * 0.28).toFixed(3) + ')';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }
    }

    function animate(now) {
        draw(now);
        win.requestAnimationFrame(animate);
    }
    win.requestAnimationFrame(animate);
})();
</script>
"""


BACKGROUND_CSS_TEMPLATE = """
<style>
:root {
    --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
    --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
    --dur-fast: 140ms;
    --dur-base: 200ms;
    --dur-page: 260ms;
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}

iframe {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: -1 !important;
    pointer-events: none !important;
    border: none !important;
}
html, body {
    background: __BG__ !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stMain"],
.stApp {
    background: transparent !important;
    color: __TEXT__ !important;
}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none !important;
}
[data-testid="InputInstructions"] {
    display: none !important;
}

/* Aurora background (Aceternity/21st.dev "Aurora Background", hand-ported to vanilla CSS) */
.aurora-bg {
    position: fixed;
    inset: 0;
    overflow: hidden;
    z-index: -2;
    pointer-events: none;
    background-image: __AURORA_BASE__, __AURORA_COLOR__;
    background-size: 300%, 200%;
    background-position: 50% 50%, 50% 50%;
    opacity: 0.5;
    filter: blur(10px) invert(__AURORA_INVERT__);
    will-change: transform;
    mask-image: radial-gradient(ellipse at 100% 0%, black 10%, transparent 70%);
    -webkit-mask-image: radial-gradient(ellipse at 100% 0%, black 10%, transparent 70%);
}
.aurora-bg::after {
    content: "";
    position: absolute;
    inset: 0;
    background-image: __AURORA_BASE__, __AURORA_COLOR__;
    background-size: 200%, 100%;
    background-attachment: fixed;
    mix-blend-mode: difference;
    animation: aurora 60s linear infinite;
}
@keyframes aurora {
    from { background-position: 50% 50%, 50% 50%; }
    to   { background-position: 350% 50%, 350% 50%; }
}

/* Layout: centered content with breathing room on both sides */
.block-container {
    max-width: 1280px !important;
    margin: 0 auto !important;
    padding-top: 2rem !important;
    animation: pageIn var(--dur-page) var(--ease-out) both;
}
@keyframes pageIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Button feedback: hover-lift + press-scale, per the animate/RECIPES.md button-press pattern */
[data-testid="stButton"] button {
    padding-left: 0.6rem !important;
    padding-right: 0.6rem !important;
    white-space: nowrap !important;
    transition: transform var(--dur-fast) var(--ease-out),
                background-color var(--dur-base) var(--ease-out),
                box-shadow var(--dur-base) var(--ease-out);
}
[data-testid="stButton"] button:hover {
    transform: translateY(-1px);
}
[data-testid="stButton"] button:active {
    transform: scale(0.97);
}

/* Ticker "heading" buttons (What You Own, Scenario Lab Holdings): bigger,
   flush-left so they line up with the description text stacked underneath */
[class*="st-key-tickerhead_"] button {
    padding-left: 0 !important;
    font-size: 1.15rem !important;
}
[class*="st-key-tickerhead_"] button p {
    font-size: 1.15rem !important;
}

/* Font scale: proportional to each element's importance */
h1 {
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    line-height: 1.05;
}
h2 {
    font-size: 1.6rem !important;
    font-weight: 600 !important;
}
h3 {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
}
[data-testid="stCaptionContainer"] {
    font-size: 0.82rem !important;
    opacity: 0.75;
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}
[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    opacity: 0.7;
}
</style>
"""


def get_background_css(colors):
    return (
        BACKGROUND_CSS_TEMPLATE
        .replace("__BG__", colors["bg"])
        .replace("__TEXT__", colors["text"])
        .replace("__AURORA_BASE__", colors["aurora_base"])
        .replace("__AURORA_COLOR__", AURORA_COLOR_GRADIENT)
        .replace("__AURORA_INVERT__", colors["aurora_invert"])
    )


def get_kinetic_grid_js(colors):
    return (
        KINETIC_GRID_TEMPLATE
        .replace("__LINE_BASE__", colors["grid_line_base_js"])
        .replace("__DOT_COLOR__", colors["grid_dot"])
    )


def render_kinetic_grid_background():
    colors = get_theme_colors()
    st.markdown(get_background_css(colors), unsafe_allow_html=True)
    st.markdown('<div class="aurora-bg"></div>', unsafe_allow_html=True)
    components.html(get_kinetic_grid_js(colors), height=0)

render_kinetic_grid_background()


# =========================================================
# AUTHENTICATION
# =========================================================

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100_000
    ).hex()


def create_user(name, email, password):
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    return tradingdb.create_user(name, email, salt, password_hash)


def authenticate(email, password):
    user = tradingdb.get_user_by_email(email)

    if not user:
        return False, None

    if hash_password(password, user["salt"]) == user["password_hash"]:
        return True, user["name"]

    return False, None


def create_session_token(email):
    token = secrets.token_urlsafe(32)
    tradingdb.set_session_token(email, token)
    return token


def validate_session_token(token):
    user = tradingdb.get_user_by_session_token(token)
    if not user:
        return None
    return user["email"], user["name"]


def clear_session_token(email):
    tradingdb.clear_session_token(email)


PASSWORD_STRENGTH_COLORS = ["#dc2626", "#ea580c", "#eab308", "#16a34a"]


def password_requirements(password, min_length=8):
    return [
        (f"At least {min_length} characters", len(password) >= min_length),
        ("Contains an uppercase letter", any(c.isupper() for c in password)),
        ("Contains a number", any(c.isdigit() for c in password)),
        ("Contains a special character", any(not c.isalnum() for c in password)),
    ]


def render_password_strength_meter(password):
    requirements = password_requirements(password)
    levels = len(requirements)
    strength = sum(1 for _, met in requirements if met) if password else 0

    bars = "".join(
        f"<div style='height:8px; flex:1; border-radius:999px; "
        f"background:{PASSWORD_STRENGTH_COLORS[strength - 1] if i < strength else 'rgba(255,255,255,0.15)'};'></div>"
        for i in range(levels)
    )

    checklist = "".join(
        f"<div style='display:flex; align-items:center; gap:0.4rem; font-size:0.8rem; "
        f"color:{'#4ADE80' if met else '#9CA3AF'}; margin-top:0.2rem;'>"
        f"<span>{'✓' if met else '•'}</span><span>{label}</span></div>"
        for label, met in requirements
    )

    st.markdown(
        f"<div id='pw-meter-static'>"
        f"<div style='display:flex; gap:4px; margin-top:0.5rem;'>{bars}</div>"
        f"<div style='margin-top:0.5rem;'>{checklist}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


LIVE_PASSWORD_STRENGTH_JS = r"""
<script>
(function () {
    try {
        var win = window.parent;
        var doc = win.document;
        var probe = doc.body.nodeName;  // throws if cross-origin blocked

        var inputs = doc.querySelectorAll('input[type="password"]');
        if (inputs.length === 0) { return; }
        var input = inputs[inputs.length - 1];

        if (input.__liveStrengthAttached) { return; }
        input.__liveStrengthAttached = true;

        var staticMeter = doc.getElementById('pw-meter-static');
        if (staticMeter) { staticMeter.style.display = 'none'; }

        var colors = ["#dc2626", "#ea580c", "#eab308", "#16a34a"];
        var requirements = [
            { label: "At least 8 characters", test: function (p) { return p.length >= 8; } },
            { label: "Contains an uppercase letter", test: function (p) { return /[A-Z]/.test(p); } },
            { label: "Contains a number", test: function (p) { return /[0-9]/.test(p); } },
            { label: "Contains a special character", test: function (p) { return /[^A-Za-z0-9]/.test(p); } }
        ];

        var meter = doc.createElement('div');
        meter.id = 'pw-meter-live';

        var wrapper = input.closest('[data-testid="stTextInput"]') || input.parentElement;
        wrapper.insertAdjacentElement('afterend', meter);

        function render() {
            var password = input.value;
            var met = requirements.map(function (r) { return r.test(password); });
            var strength = password ? met.filter(Boolean).length : 0;

            var bars = '';
            for (var i = 0; i < requirements.length; i++) {
                var bg = i < strength ? colors[strength - 1] : 'rgba(255,255,255,0.15)';
                bars += '<div style="height:8px; flex:1; border-radius:999px; background:' + bg + ';"></div>';
            }

            var checklist = '';
            for (var j = 0; j < requirements.length; j++) {
                var color = met[j] ? '#4ADE80' : '#9CA3AF';
                var mark = met[j] ? '✓' : '•';
                checklist += '<div style="display:flex; align-items:center; gap:0.4rem; font-size:0.8rem; color:' + color + '; margin-top:0.2rem;"><span>' + mark + '</span><span>' + requirements[j].label + '</span></div>';
            }

            meter.innerHTML =
                '<div style="display:flex; gap:4px; margin-top:0.5rem;">' + bars + '</div>' +
                '<div style="margin-top:0.5rem;">' + checklist + '</div>';
        }

        input.addEventListener('input', render);
        render();
    } catch (err) {
        // Cross-frame access blocked by the browser — the static,
        // Enter/blur-triggered meter remains visible as a fallback.
    }
})();
</script>
"""


def render_live_password_strength_script():
    components.html(LIVE_PASSWORD_STRENGTH_JS, height=0)


AUTH_QUOTES = {
    "sign_in": ("Welcome back. The journey continues.", "PortfolioLab"),
    "sign_up": ("Investing is understanding, not guessing.", "PortfolioLab"),
}


NYSE_PHOTO_URL = "https://upload.wikimedia.org/wikipedia/commons/4/43/NYC_-_New_York_Stock_Exchange.JPG"


def render_auth_quote_panel(mode):
    quote, author = AUTH_QUOTES[mode]

    st.markdown(
        f"""
        <div style='position:relative; height:100%; min-height:480px; border-radius:16px;
                    overflow:hidden; animation: pageIn 340ms var(--ease-out, ease-out) both;'>
            <img src="{NYSE_PHOTO_URL}"
                 style='position:absolute; inset:0; width:100%; height:100%;
                        object-fit:cover; z-index:0;'>
            <div style='position:absolute; inset:0; z-index:1;
                        background: linear-gradient(160deg, rgba(27,42,74,0.55) 0%, rgba(16,16,20,0.85) 100%);'>
            </div>
            <div style='position:relative; z-index:2; height:100%; display:flex;
                        align-items:flex-end; justify-content:center;
                        padding:2.5rem; text-align:center;'>
                <div>
                    <p style='font-size:1.3rem; font-weight:600; color:#FAFAFA; line-height:1.4;'>
                        "{quote}"
                    </p>
                    <p style='font-size:0.85rem; color:#8FBFFF; margin-top:0.5rem;'>— {author}</p>
                </div>
            </div>
        </div>
        <p style='font-size:0.65rem; opacity:0.5; text-align:right; margin-top:0.3rem;'>
            NYSE photo: Jean-Christophe BENOIST, CC BY 3.0
        </p>
        """,
        unsafe_allow_html=True
    )


def render_sign_in_form():
    st.markdown("### Sign in to your account")
    st.caption("Enter your email below to sign in")

    email = st.text_input("Email", placeholder="you@example.com", key="signin_email")
    password = st.text_input("Password", type="password", placeholder="Password", key="signin_password")

    if st.button("Sign In", type="primary", width="stretch"):
        if not email or not password:
            st.error("Please fill in both fields.")
        else:
            ok, name = authenticate(email, password)
            if ok:
                st.session_state["auth_logged_in"] = True
                st.session_state["auth_name"] = name
                st.session_state["auth_email"] = email.strip().lower()
                st.query_params["token"] = create_session_token(email)
                st.rerun()
            else:
                st.error("Incorrect email or password.")

    st.write("Don't have an account?")
    if st.button("Sign up", type="tertiary", key="switch_to_signup"):
        st.session_state["auth_mode"] = "sign_up"
        st.rerun()


def render_sign_up_form():
    st.markdown("### Create an account")
    st.caption("Enter your details below to sign up")

    name = st.text_input("Full Name", placeholder="John Doe", key="signup_name")
    email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
    password = st.text_input("Password", type="password", placeholder="Password", key="signup_password")

    render_password_strength_meter(password)
    render_live_password_strength_script()

    if st.button("Sign Up", type="primary", width="stretch"):
        if not name or not email or not password:
            st.error("Please fill in all fields.")
        else:
            ok, message = create_user(name, email, password)
            if ok:
                st.session_state["auth_logged_in"] = True
                st.session_state["auth_name"] = name.strip()
                st.session_state["auth_email"] = email.strip().lower()
                st.query_params["token"] = create_session_token(email)
                st.rerun()
            else:
                st.error(message)

    st.write("Already have an account?")
    if st.button("Sign in", type="tertiary", key="switch_to_signin"):
        st.session_state["auth_mode"] = "sign_in"
        st.rerun()


def render_auth_screen():
    st.session_state.setdefault("auth_mode", "sign_in")

    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)

    col_form, col_quote = st.columns([1, 1], gap="large")

    with col_form:
        _, form_center, _ = st.columns([1, 3, 1])
        with form_center:
            if st.session_state["auth_mode"] == "sign_in":
                render_sign_in_form()
            else:
                render_sign_up_form()

    with col_quote:
        render_auth_quote_panel(st.session_state["auth_mode"])


if "auth_logged_in" not in st.session_state:
    st.session_state["auth_logged_in"] = False

if not st.session_state["auth_logged_in"]:
    token_result = validate_session_token(st.query_params.get("token"))
    if token_result:
        auto_email, auto_name = token_result
        st.session_state["auth_logged_in"] = True
        st.session_state["auth_name"] = auto_name
        st.session_state["auth_email"] = auto_email

if not st.session_state["auth_logged_in"]:
    render_auth_screen()
    st.stop()


# =========================================================
# PORTFOLIO DEFINITIONS
# =========================================================

portfolios = {

    "Conservative": {
        "VOO": 0.40,
        "BND": 0.40,
        "VXUS": 0.20
    },

    "Moderate": {
        "VOO": 0.50,
        "QQQ": 0.20,
        "VXUS": 0.20,
        "BND": 0.10
    },

    "Aggressive": {
        "VOO": 0.40,
        "QQQ": 0.30,
        "VXUS": 0.20,
        "BND": 0.10
    }
}


# =========================================================
# TOP NAVIGATION
# =========================================================

st.markdown(
    "<div style='display:flex; align-items:center; justify-content:center; gap:0.5rem;'>"
    "<svg width='26' height='26' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'>"
    "<rect x='3' y='12' width='4' height='9' rx='1' fill='#4A9EFF'/>"
    "<rect x='10' y='7' width='4' height='14' rx='1' fill='#4A9EFF'/>"
    "<rect x='17' y='3' width='4' height='18' rx='1' fill='#4A9EFF'/>"
    "</svg>"
    "<h2 style='margin:0;'>PortfolioLab</h2>"
    "</div>"
    "<p style='text-align:center; opacity:0.75; font-size:0.85rem; margin-top:0.2rem;'>"
    "Simple portfolio analytics for first-time investors."
    "</p>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    .st-key-topright_account {
        position: fixed;
        top: 1.1rem;
        right: 1.75rem;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.15rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.container(key="topright_account"):
    theme_toggle_label = "Light mode" if st.session_state["theme"] == "dark" else "Dark mode"
    if st.button(theme_toggle_label, type="tertiary", key="theme_toggle"):
        st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
        st.rerun()
    if st.button("Log out", type="tertiary", key="top_logout"):
        clear_session_token(st.session_state.get("auth_email"))
        st.session_state["auth_logged_in"] = False
        if "token" in st.query_params:
            del st.query_params["token"]
        st.rerun()
    st.caption(f"Signed in as **{st.session_state.get('auth_name', 'User')}**")

st.session_state.setdefault("current_page", "Overview")

NAV_OPTIONS = [
    "Overview",
    "Portfolio",
    "Performance",
    "Risk",
    "ETF Research",
    "Scenario Lab",
    "About"
]

nav_cols = st.columns(len(NAV_OPTIONS))

for nav_col, option in zip(nav_cols, NAV_OPTIONS):
    with nav_col:
        is_active = st.session_state["current_page"] == option
        if st.button(
            option,
            key=f"nav_{option}",
            type="primary" if is_active else "tertiary",
            width="stretch"
        ):
            st.session_state["current_page"] = option
            st.rerun()

page = st.session_state["current_page"]

st.markdown(
    "<hr style='border:none; border-top:2px solid rgba(255,255,255,0.2); "
    "margin-top:1rem; margin-bottom:1.5rem;'>",
    unsafe_allow_html=True
)

st.session_state.setdefault("global_amount", 100.0)
st.session_state.setdefault("global_risk", "Conservative")

amount = st.session_state["global_amount"]
risk = st.session_state["global_risk"]


def render_portfolio_settings():
    settings_col1, settings_col2 = st.columns(2)

    with settings_col1:
        st.number_input(
            "Investment amount",
            min_value=10.0,
            step=10.0,
            key="global_amount"
        )

    with settings_col2:
        st.selectbox(
            "Risk tolerance",
            [
                "Conservative",
                "Moderate",
                "Aggressive"
            ],
            key="global_risk"
        )

    st.caption(
        "Adjust your investment amount and risk tolerance "
        "to explore different hypothetical portfolios."
    )

    st.divider()


# =========================================================
# SELECT PORTFOLIO
# =========================================================

st.session_state.setdefault("custom_holdings", {})

preset_dollar_holdings = {
    ticker: weight * amount
    for ticker, weight in portfolios[risk].items()
}

combined_dollar_holdings = dict(preset_dollar_holdings)

for ticker, custom_amount in st.session_state["custom_holdings"].items():
    combined_dollar_holdings[ticker] = (
        combined_dollar_holdings.get(ticker, 0) + custom_amount
    )

total_invested = sum(combined_dollar_holdings.values())

portfolio = {
    ticker: dollar_amount / total_invested
    for ticker, dollar_amount in combined_dollar_holdings.items()
}


# =========================================================
# DOWNLOAD HISTORICAL DATA
# =========================================================

prices = yf.download(
    list(portfolio.keys()),
    period="5y",
    auto_adjust=True,
    progress=False
)


# =========================================================
# CLEAN PRICE DATA
# =========================================================

returns = prices["Close"].pct_change().dropna()


# =========================================================
# PORTFOLIO RETURN CALCULATION
# =========================================================

portfolio_returns = pd.Series(
    0.0,
    index=returns.index
)

for ticker, weight in portfolio.items():

    portfolio_returns += (
        returns[ticker] * weight
    )


# =========================================================
# PORTFOLIO GROWTH
# =========================================================

portfolio_growth = (
    1 + portfolio_returns
).cumprod()


final_value = (
    total_invested * portfolio_growth.iloc[-1]
)


total_return = (
    portfolio_growth.iloc[-1] - 1
)


# =========================================================
# S&P 500 BENCHMARK
# =========================================================

benchmark_returns = returns["VOO"]

benchmark_growth = (
    1 + benchmark_returns
).cumprod()


benchmark_value = (
    total_invested * benchmark_growth.iloc[-1]
)


benchmark_return = (
    benchmark_growth.iloc[-1] - 1
)


# =========================================================
# RISK CALCULATIONS
# =========================================================

annualized_volatility = (
    portfolio_returns.std()
    * (252 ** 0.5)
)


risk_score = min(
    10,
    max(
        1,
        annualized_volatility * 20
    )
)


# =========================================================
# MAXIMUM DRAWDOWN
# =========================================================

running_peak = (
    portfolio_growth.cummax()
)

drawdown = (
    portfolio_growth / running_peak
) - 1


maximum_drawdown = drawdown.min()


# =========================================================
# ETF INFORMATION
# =========================================================

etf_information = {

    "VOO": {
        "name": "Vanguard S&P 500 ETF",
        "asset_class": "U.S. Equities",
        "focus": "Large-cap U.S. companies",
        "role": "Core equity exposure",
        "description": (
            "Tracks the S&P 500, giving broad exposure to 500 of the largest "
            "U.S. companies across nearly every sector. It's often used as a "
            "core holding because of its low cost and broad diversification."
        )
    },

    "QQQ": {
        "name": "Invesco QQQ",
        "asset_class": "U.S. Equities",
        "focus": "Nasdaq-100 companies",
        "role": "Growth and technology exposure",
        "description": (
            "Tracks the Nasdaq-100, which is heavily weighted toward "
            "technology and other growth-oriented companies. It has "
            "historically offered higher growth potential alongside "
            "higher volatility than the broader market."
        )
    },

    "VXUS": {
        "name": "Vanguard Total International Stock ETF",
        "asset_class": "International Equities",
        "focus": "Companies outside the United States",
        "role": "International diversification",
        "description": (
            "Provides exposure to thousands of companies across developed "
            "and emerging markets outside the U.S., helping diversify a "
            "portfolio away from U.S.-only risk."
        )
    },

    "BND": {
        "name": "Vanguard Total Bond Market ETF",
        "asset_class": "Fixed Income",
        "focus": "U.S. investment-grade bonds",
        "role": "Income and portfolio stability",
        "description": (
            "Holds a broad mix of U.S. investment-grade bonds, providing "
            "steady income and helping cushion a portfolio during stock "
            "market downturns."
        )
    }
}


SP500_FALLBACK = [
    ("AAPL", "Apple Inc.", "Information Technology"),
    ("MSFT", "Microsoft Corp.", "Information Technology"),
    ("NVDA", "NVIDIA Corp.", "Information Technology"),
    ("GOOGL", "Alphabet Inc.", "Communication Services"),
    ("AMZN", "Amazon.com Inc.", "Consumer Discretionary"),
    ("META", "Meta Platforms Inc.", "Communication Services"),
    ("TSLA", "Tesla Inc.", "Consumer Discretionary"),
    ("JPM", "JPMorgan Chase & Co.", "Financials"),
    ("JNJ", "Johnson & Johnson", "Health Care"),
    ("XOM", "Exxon Mobil Corp.", "Energy"),
]


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_sp500_list():
    try:
        import urllib.request
        import io

        req = urllib.request.Request(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        html = urllib.request.urlopen(req, timeout=15).read()
        tables = pd.read_html(io.BytesIO(html))
        df = tables[0]

        rows = list(zip(df["Symbol"], df["Security"], df["GICS Sector"]))
        rows = [(str(t).replace(".", "-"), str(n), str(s)) for t, n, s in rows]
        return sorted(rows, key=lambda r: r[1])
    except Exception:
        return SP500_FALLBACK


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_company_info(ticker):
    try:
        info = yf.Ticker(ticker).info
        summary = info.get("longBusinessSummary", "")
        if summary and len(summary) > 220:
            summary = summary[:220].rsplit(" ", 1)[0] + "…"

        return {
            "name": info.get("longName") or info.get("shortName") or ticker,
            "asset_class": "Equity",
            "focus": info.get("sector") or info.get("industry") or "Individual stock",
            "role": "User-added holding",
            "description": summary or f"{ticker} is a stock you've added to your portfolio."
        }
    except Exception:
        return {
            "name": ticker,
            "asset_class": "Equity",
            "focus": "Individual stock",
            "role": "User-added holding",
            "description": f"{ticker} is a stock you've added to your portfolio."
        }


def get_ticker_display_info(ticker):
    if ticker in etf_information:
        return etf_information[ticker]
    return fetch_company_info(ticker)


def render_add_stock_section():
    st.subheader("Add a Stock")
    st.caption("Add any S&P 500 company to your portfolio with its own dollar amount.")

    sp500 = fetch_sp500_list()
    sectors = sorted(set(sector for _, _, sector in sp500))

    selected_sectors = st.multiselect(
        "Filter by sector",
        sectors,
        placeholder="All sectors"
    )

    filtered = [
        (ticker, name) for ticker, name, sector in sp500
        if not selected_sectors or sector in selected_sectors
    ]

    if not filtered:
        st.info("No companies match the selected sector filter.")
        return

    options = [f"{ticker} — {name}" for ticker, name in filtered]

    add_col1, add_col2, add_col3 = st.columns([3, 1, 1])

    with add_col1:
        selected_option = st.selectbox("Choose a stock", options, key="add_stock_select")

    with add_col2:
        stock_amount = st.number_input(
            "Amount ($)", min_value=10.0, value=100.0, step=10.0, key="add_stock_amount"
        )

    with add_col3:
        st.write("")
        st.write("")
        if st.button("Add to Portfolio", type="primary"):
            ticker = selected_option.split(" — ")[0]
            st.session_state["custom_holdings"][ticker] = (
                st.session_state["custom_holdings"].get(ticker, 0) + stock_amount
            )
            st.rerun()

    if st.session_state["custom_holdings"]:
        st.write("**Your added stocks:**")

        for ticker, custom_amount in list(st.session_state["custom_holdings"].items()):
            remove_col1, remove_col2, remove_col3 = st.columns([1, 1, 1])

            with remove_col1:
                st.write(f"**{ticker}**")

            with remove_col2:
                st.write(f"${custom_amount:,.2f}")

            with remove_col3:
                if st.button("Remove", key=f"remove_custom_{ticker}", type="tertiary"):
                    del st.session_state["custom_holdings"][ticker]
                    st.rerun()

    st.divider()


# =========================================================
# TICKER DETAIL POPUP
# =========================================================

TICKER_RANGES = [
    ("Day", "1d", "5m"),
    ("Week", "5d", "30m"),
    ("Month", "1mo", "1d"),
    ("Year", "1y", "1d"),
    ("YTD", "ytd", "1d"),
]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ticker_history(ticker, period, interval):
    return yf.Ticker(ticker).history(period=period, interval=interval)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ticker_fast_info(ticker):
    info = yf.Ticker(ticker).fast_info
    return {
        "last_price": info.get("lastPrice"),
        "previous_close": info.get("previousClose"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "year_high": info.get("yearHigh"),
        "year_low": info.get("yearLow"),
        "market_cap": info.get("marketCap"),
        "volume": info.get("lastVolume"),
    }


@st.dialog("Stock Detail", width="large")
def ticker_dialog(ticker):

    name = etf_information.get(ticker, {}).get("name", ticker)
    st.subheader(f"{ticker} — {name}")

    try:
        stats = fetch_ticker_fast_info(ticker)
    except Exception:
        stats = None

    if stats and stats.get("last_price") is not None:
        last_price = stats["last_price"]
        prev_close = stats.get("previous_close")

        stat1, stat2, stat3, stat4 = st.columns(4)

        with stat1:
            if prev_close:
                change = last_price - prev_close
                change_pct = (change / prev_close) * 100
                st.metric(
                    "Price",
                    f"${last_price:,.2f}",
                    f"{change:+.2f} ({change_pct:+.2f}%)"
                )
            else:
                st.metric("Price", f"${last_price:,.2f}")

        with stat2:
            if stats.get("day_high") and stats.get("day_low"):
                st.metric("Day Range", f"${stats['day_low']:,.2f} – ${stats['day_high']:,.2f}")

        with stat3:
            if stats.get("year_high") and stats.get("year_low"):
                st.metric("52-Week Range", f"${stats['year_low']:,.2f} – ${stats['year_high']:,.2f}")

        with stat4:
            if stats.get("market_cap"):
                st.metric("Market Cap", f"${stats['market_cap'] / 1e9:,.1f}B")
            elif stats.get("volume"):
                st.metric("Volume", f"{stats['volume']:,.0f}")

        st.divider()
    else:
        st.warning("Live stats are temporarily unavailable for this ticker.")

    tabs = st.tabs([label for label, _, _ in TICKER_RANGES])

    for tab, (label, period, interval) in zip(tabs, TICKER_RANGES):
        with tab:
            try:
                hist = fetch_ticker_history(ticker, period, interval)
            except Exception:
                hist = None

            if hist is None or hist.empty:
                st.info("No price data available for this range (market may be closed).")
                continue

            line_chart_single(hist["Close"], height=300, y_title="Price ($)")

            range_return = (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100
            st.caption(f"{label} change: {range_return:+.2f}%")

    st.divider()
    st.caption(get_ticker_display_info(ticker)["focus"])


def ticker_button(ticker, key_suffix, label=None, heading=False):
    if heading:
        with st.container(key=f"tickerhead_{key_suffix}_{ticker}"):
            if st.button(label or ticker, key=f"tkr_{ticker}_{key_suffix}", type="tertiary"):
                ticker_dialog(ticker)
    else:
        if st.button(label or ticker, key=f"tkr_{ticker}_{key_suffix}", type="tertiary"):
            ticker_dialog(ticker)


def extract_close_series(prices_df, ticker):
    close = prices_df["Close"]

    if isinstance(close, pd.Series):
        return close

    if isinstance(close.columns, pd.MultiIndex):
        if ticker in close.columns.get_level_values(-1):
            return close.xs(ticker, axis=1, level=-1).iloc[:, 0]
        return close.iloc[:, 0]

    if ticker in close.columns:
        return close[ticker]

    # yfinance has been observed to name the single remaining column
    # inconsistently across calls within the same process (varies by
    # whether the ticker was already fetched as part of a different
    # multi-ticker batch earlier in the same run). With only one column
    # present, it must be the ticker's data regardless of its label.
    return close.iloc[:, 0]


def line_chart_single(series, height=350, y_title="Value ($)"):
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    df = pd.DataFrame({"Date": series.index, "Value": series.values})

    nearest = alt.selection_point(on="mouseover", nearest=True, fields=["Date"], empty=False)

    line = (
        alt.Chart(df)
        .mark_line(color="#4A9EFF", strokeWidth=2, interpolate="monotone")
        .encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("Value:Q", title=y_title, scale=alt.Scale(zero=False)),
        )
    )

    area = line.mark_area(
        interpolate="monotone",
        line=False,
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(74,158,255,0.35)", offset=0),
                alt.GradientStop(color="rgba(74,158,255,0)", offset=1),
            ],
            x1=1, x2=1, y1=1, y2=0,
        ),
    ).encode(
        y2=alt.value(height)
    )

    points = (
        line.mark_point(size=45, color="#4A9EFF", filled=True)
        .encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
            tooltip=[alt.Tooltip("Date:T", title="Date"), alt.Tooltip("Value:Q", title="Value", format=",.2f")]
        )
        .add_params(nearest)
    )

    chart = (
        (area + line + points)
        .properties(height=height, padding={"left": 5, "right": 5, "top": 5, "bottom": 28})
    )
    st.altair_chart(chart, use_container_width=True)


def line_chart_multi(df, height=400, y_title="Value ($)"):
    frames = [
        pd.DataFrame({"Date": df.index, "Series": col, "Value": df[col].values})
        for col in df.columns
    ]
    long_df = pd.concat(frames, ignore_index=True)

    nearest = alt.selection_point(on="mouseover", nearest=True, fields=["Date"], empty=False)

    line = (
        alt.Chart(long_df)
        .mark_line(strokeWidth=2, interpolate="monotone")
        .encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("Value:Q", title=y_title, scale=alt.Scale(zero=False)),
            color=alt.Color("Series:N", title=None),
        )
    )

    points = (
        line.mark_point(size=45, filled=True)
        .encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
            tooltip=["Date:T", "Series:N", alt.Tooltip("Value:Q", title="Value", format=",.2f")]
        )
        .add_params(nearest)
    )

    chart = (
        (line + points)
        .properties(height=height, padding={"left": 5, "right": 5, "top": 5, "bottom": 28})
    )
    st.altair_chart(chart, use_container_width=True)


# =========================================================
# OVERVIEW PAGE
# =========================================================

if page == "Overview":

    st.caption("PERSONAL PORTFOLIO ANALYTICS")

    st.title("Build. Analyze. Understand.")

    render_portfolio_settings()

    st.write(
        "A simple portfolio research tool that helps "
        "first-time investors explore allocation, "
        "performance, and risk."
    )

    st.divider()

    # ---------------------------------------------
    # PORTFOLIO SUMMARY
    # ---------------------------------------------

    st.subheader(
        f"{risk} Portfolio"
    )

    st.caption(
        "Five-year historical analysis"
    )

    overview1, overview2, overview3, overview4 = st.columns(4)

    with overview1:

        st.metric(
            "Investment",
            f"${total_invested:,.2f}"
        )

    with overview2:

        st.metric(
            "Historical Value",
            f"${final_value:,.2f}",
            f"{total_return * 100:+.2f}%"
        )

    with overview3:

        st.metric(
            "S&P 500 Value",
            f"${benchmark_value:,.2f}"
        )

    with overview4:

        st.metric(
            "Risk Score",
            f"{risk_score:.1f}/10"
        )

    st.divider()

    # ---------------------------------------------
    # GROWTH CHART
    # ---------------------------------------------

    st.subheader(
        "How Your Investment Could Have Grown"
    )

    overview_chart = pd.DataFrame(
        {
            "Your Portfolio":
                portfolio_growth * total_invested,

            "S&P 500":
                benchmark_growth * total_invested
        }
    )

    line_chart_multi(overview_chart, height=400)

    st.caption(
        "Historical simulation based on the selected "
        "portfolio allocation. This is not a prediction."
    )

    st.divider()

    # ---------------------------------------------
    # PORTFOLIO SNAPSHOT
    # ---------------------------------------------

    st.subheader(
        "Portfolio Snapshot"
    )

    snapshot_col1, snapshot_col2 = st.columns(2)

    with snapshot_col1:

        st.write("**Allocation**")

        for ticker, weight in portfolio.items():

            alloc_col1, alloc_col2 = st.columns([1, 2])

            with alloc_col1:
                ticker_button(ticker, key_suffix="overview")

            with alloc_col2:
                st.write(f"{weight * 100:.0f}%")

    with snapshot_col2:

        st.write("**Risk Profile**")

        if risk == "Conservative":

            st.write(
                "Lower-risk allocation with a larger "
                "bond position."
            )

        elif risk == "Moderate":

            st.write(
                "Balanced exposure across U.S. equities, "
                "international equities, growth stocks, "
                "and bonds."
            )

        else:

            st.write(
                "Higher equity exposure designed for "
                "greater long-term growth potential "
                "with increased volatility."
            )


# =========================================================
# PORTFOLIO PAGE
# =========================================================

elif page == "Portfolio":

    st.caption("PORTFOLIO CONSTRUCTION")

    st.title("Your Portfolio")

    render_portfolio_settings()

    st.write(
        f"Your **{risk.lower()}** portfolio distributes "
        f"${total_invested:,.2f} across {len(portfolio)} holdings."
    )

    st.divider()

    # ---------------------------------------------
    # HOLDINGS
    # ---------------------------------------------

    st.subheader("Holdings")

    allocation_data = pd.DataFrame(
        {
            "Ticker": list(portfolio.keys()),

            "Allocation": [
                weight * 100
                for weight in portfolio.values()
            ],

            "Investment": [
                total_invested * weight
                for weight in portfolio.values()
            ]
        }
    )

    allocation_display = allocation_data.copy()

    allocation_display["Allocation"] = (
        allocation_display["Allocation"]
        .map(lambda x: f"{x:.0f}%")
    )

    allocation_display["Investment"] = (
        allocation_display["Investment"]
        .map(lambda x: f"${x:,.2f}")
    )

    st.dataframe(
        allocation_display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    render_add_stock_section()

    # ---------------------------------------------
    # PORTFOLIO VALUE
    # ---------------------------------------------

    st.subheader("Portfolio Value")

    line_chart_single(portfolio_growth * total_invested, height=350)

    st.caption(
        "Historical value of this portfolio over the trailing five years."
    )

    st.divider()

    # ---------------------------------------------
    # ALLOCATION CHART
    # ---------------------------------------------

    st.subheader("Allocation Breakdown")

    chart_data = pd.DataFrame(
        {
            "Allocation": [
                weight * 100
                for weight in portfolio.values()
            ]
        },
        index=portfolio.keys()
    )

    st.bar_chart(
        chart_data,
        height=350
    )

    st.divider()

    # ---------------------------------------------
    # ETF DESCRIPTIONS
    # ---------------------------------------------

    st.subheader("What You Own")

    for ticker in portfolio.keys():

        info = get_ticker_display_info(ticker)

        ticker_button(ticker, key_suffix="whatyouown", label=f"**{ticker}**", heading=True)

        st.markdown(
            f"<div style='font-size:1.05rem; line-height:1.55; color:#FAFAFA; "
            f"margin-bottom:0.6rem;'>"
            f"<strong>{info['name']}</strong> — {info['description']}"
            f"</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"<div style='font-size:0.85rem; color:#8FBFFF; margin-top:0.4rem;'>"
            f"{info['role']} · {info['focus']}"
            f"</div>",
            unsafe_allow_html=True
        )

        st.divider()


# =========================================================
# PERFORMANCE PAGE
# =========================================================

elif page == "Performance":

    st.caption("HISTORICAL PERFORMANCE")

    st.title("Performance")

    render_portfolio_settings()

    st.write(
        "See how your hypothetical portfolio would have "
        "performed over the past five years compared "
        "with the S&P 500."
    )

    st.divider()

    # ---------------------------------------------
    # PERFORMANCE METRICS
    # ---------------------------------------------

    portfolio_return_pct = (
        total_return * 100
    )

    benchmark_return_pct = (
        benchmark_return * 100
    )

    relative_performance = (
        portfolio_return_pct
        - benchmark_return_pct
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Portfolio Return",
            f"{portfolio_return_pct:+.2f}%"
        )

    with col2:

        st.metric(
            "S&P 500 Return",
            f"{benchmark_return_pct:+.2f}%"
        )

    with col3:

        st.metric(
            "Difference vs. S&P 500",
            f"{relative_performance:+.2f}%"
        )

    st.divider()

    # ---------------------------------------------
    # PORTFOLIO GROWTH
    # ---------------------------------------------

    st.subheader("Portfolio Growth")

    portfolio_value = (
        portfolio_growth * total_invested
    )

    line_chart_single(portfolio_value, height=400)

    st.caption(
        "Historical value of the hypothetical portfolio "
        "assuming the original allocation remained constant."
    )

    st.divider()

    # ---------------------------------------------
    # BENCHMARK COMPARISON
    # ---------------------------------------------

    st.subheader("Portfolio vs. S&P 500")

    comparison = pd.DataFrame(
        {
            "Your Portfolio":
                portfolio_growth * total_invested,

            "S&P 500":
                benchmark_growth * total_invested
        }
    )

    line_chart_multi(comparison, height=400)

    st.divider()

    # ---------------------------------------------
    # DAILY PERFORMANCE
    # ---------------------------------------------

    st.subheader("Daily Performance")

    best_day = (
        portfolio_returns.max() * 100
    )

    worst_day = (
        portfolio_returns.min() * 100
    )

    day_col1, day_col2 = st.columns(2)

    with day_col1:

        st.metric(
            "Best Day",
            f"{best_day:+.2f}%"
        )

    with day_col2:

        st.metric(
            "Worst Day",
            f"{worst_day:+.2f}%"
        )


# =========================================================
# RISK PAGE
# =========================================================

elif page == "Risk":

    st.caption("PORTFOLIO RISK ANALYSIS")

    st.title("Understand Your Risk")

    render_portfolio_settings()

    st.write(
        "Evaluate the historical volatility and downside "
        "risk associated with your portfolio."
    )

    st.divider()

    # ---------------------------------------------
    # RISK METRICS
    # ---------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Risk Score",
            f"{risk_score:.1f} / 10"
        )

    with col2:

        st.metric(
            "Annualized Volatility",
            f"{annualized_volatility * 100:.2f}%"
        )

    with col3:

        st.metric(
            "Maximum Drawdown",
            f"{maximum_drawdown * 100:.2f}%"
        )

    st.divider()

    # ---------------------------------------------
    # DRAWDOWN CHART
    # ---------------------------------------------

    st.subheader("Historical Drawdown")

    drawdown_chart = (
        drawdown * 100
    )

    st.area_chart(
        drawdown_chart,
        height=350
    )

    st.caption(
        "Drawdown measures the decline from a previous "
        "portfolio peak."
    )

    st.divider()

    # ---------------------------------------------
    # RISK INTERPRETATION
    # ---------------------------------------------

    st.subheader("Risk Interpretation")

    if risk_score < 4:

        st.success(
            "This portfolio has historically experienced "
            "relatively low volatility."
        )

    elif risk_score < 7:

        st.info(
            "This portfolio has historically experienced "
            "moderate volatility."
        )

    else:

        st.warning(
            "This portfolio has historically experienced "
            "relatively high volatility."
        )

    st.write(
        f"**Annualized volatility:** "
        f"{annualized_volatility * 100:.2f}%"
    )

    st.write(
        f"**Maximum historical drawdown:** "
        f"{maximum_drawdown * 100:.2f}%"
    )

    st.caption(
        "The risk score is a simplified educational measure "
        "based on historical portfolio volatility. It is not "
        "an official investment risk rating."
    )


# =========================================================
# ETF RESEARCH PAGE
# =========================================================

elif page == "ETF Research":

    st.caption("ETF RESEARCH")

    st.title("Explore Your ETFs")

    render_portfolio_settings()

    st.write(
        "Learn what each ETF in your portfolio is designed "
        "to provide exposure to."
    )

    st.divider()

    # ---------------------------------------------
    # ETF SELECTOR
    # ---------------------------------------------

    selected_etf = st.selectbox(
        "Select a holding",
        list(portfolio.keys())
    )

    info = get_ticker_display_info(selected_etf)

    st.subheader(
        f"{selected_etf} — {info['name']}"
    )

    ticker_button(selected_etf, key_suffix="etfresearch", label="View Chart & Stats")

    # ---------------------------------------------
    # ETF DETAILS
    # ---------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Asset Class",
            info["asset_class"]
        )

    with col2:

        st.metric(
            "Investment Focus",
            info["focus"]
        )

    with col3:

        st.metric(
            "Portfolio Role",
            info["role"]
        )

    st.divider()

    # ---------------------------------------------
    # HISTORICAL DATA
    # ---------------------------------------------

    st.subheader("Historical Performance")

    etf_prices = yf.download(
        [selected_etf],
        period="5y",
        auto_adjust=True,
        progress=False
    )

    etf_close = extract_close_series(etf_prices, selected_etf)

    etf_returns = (
        etf_close
        .pct_change()
        .dropna()
    )

    etf_growth = (
        1 + etf_returns
    ).cumprod()

    etf_return = (
        etf_growth.iloc[-1] - 1
    )

    current_price = (
        etf_close.iloc[-1]
    )

    metric1, metric2 = st.columns(2)

    with metric1:

        st.metric(
            "Current Price",
            f"${float(current_price):,.2f}"
        )

    with metric2:

        st.metric(
            "5-Year Return",
            f"{float(etf_return) * 100:+.2f}%"
        )

    st.subheader("Historical Price")

    line_chart_single(etf_close, height=400, y_title="Price ($)")

    # ---------------------------------------------
    # USER EXPOSURE
    # ---------------------------------------------

    if selected_etf in portfolio:

        weight = portfolio[selected_etf]

        investment = (
            total_invested * weight
        )

        st.divider()

        st.subheader("Your Exposure")

        exposure_col1, exposure_col2 = st.columns(2)

        with exposure_col1:

            st.metric(
                "Portfolio Allocation",
                f"{weight * 100:.0f}%"
            )

        with exposure_col2:

            st.metric(
                "Your Investment",
                f"${investment:,.2f}"
            )

        st.info(
            f"{selected_etf} represents "
            f"{weight * 100:.0f}% of your current "
            f"hypothetical portfolio."
        )


# =========================================================
# SCENARIO LAB PAGE
# =========================================================

elif page == "Scenario Lab":

    st.caption("TRADING ARENA")

    st.title("Scenario Lab")

    st.write(
        "Trade real stocks with virtual cash, compete on the leaderboard, "
        "and complete challenges for bonus points and cash."
    )

    player_email = st.session_state["auth_email"]
    player_name = st.session_state["auth_name"]

    trading_player = tradingdb.get_or_create_player(player_email, player_name)
    tradingdb.seed_default_challenges_if_empty()

    try:
        portfolio_value = tradingdb.get_portfolio_value_now(player_email)
    except Exception:
        portfolio_value = float(trading_player["cash_balance"])

    starting_cash = float(trading_player["starting_cash"])
    total_return_pct = (
        (portfolio_value - starting_cash) / starting_cash * 100
        if starting_cash else 0
    )

    try:
        newly_completed = tradingdb.check_and_complete_challenges(player_email, portfolio_value)
        if newly_completed:
            trading_player = tradingdb.get_player(player_email)
    except Exception:
        newly_completed = []

    for title in newly_completed:
        st.success(f"Challenge completed: {title}! Reward added to your account.")

    st.divider()

    # ---------------------------------------------
    # PORTFOLIO SUMMARY
    # ---------------------------------------------

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

    with summary_col1:
        st.metric("Cash", f"${float(trading_player['cash_balance']):,.2f}")

    with summary_col2:
        st.metric(
            "Portfolio Value",
            f"${portfolio_value:,.2f}",
            f"{total_return_pct:+.2f}%"
        )

    with summary_col3:
        st.metric("Points", f"{float(trading_player['total_points']):,.0f}")

    with summary_col4:
        st.metric("Started Trading", trading_player["created_at"].strftime("%b %d, %Y"))

    st.divider()

    # ---------------------------------------------
    # PORTFOLIO GROWTH
    # ---------------------------------------------

    st.subheader("Portfolio Growth")

    try:
        trading_history = tradingdb.get_portfolio_history(player_email)
        if len(trading_history) > 1:
            line_chart_single(trading_history, height=350)
        else:
            st.info("Make a trade to start tracking your portfolio's growth over time.")
    except Exception:
        st.info("Portfolio history isn't available right now.")

    st.divider()

    # ---------------------------------------------
    # TRADE
    # ---------------------------------------------

    st.subheader("Trade")

    trade_tab1, trade_tab2, trade_tab3 = st.tabs(["Buy", "Sell", "Holdings"])

    with trade_tab1:

        sp500 = fetch_sp500_list()
        sectors = sorted(set(sector for _, _, sector in sp500))

        buy_sectors = st.multiselect(
            "Filter by sector", sectors, placeholder="All sectors", key="trade_sector_filter"
        )

        filtered = [
            (ticker, name) for ticker, name, sector in sp500
            if not buy_sectors or sector in buy_sectors
        ]

        if not filtered:
            st.info("No companies match the selected sector filter.")
        else:
            options = [f"{ticker} — {name}" for ticker, name in filtered]

            buy_col1, buy_col2 = st.columns([3, 1])

            with buy_col1:
                selected_buy_option = st.selectbox("Choose a stock", options, key="buy_stock_select")

            buy_ticker = selected_buy_option.split(" — ")[0]

            try:
                buy_live_price = tradingdb.fetch_current_prices([buy_ticker]).get(buy_ticker)
            except Exception:
                buy_live_price = None

            with buy_col2:
                st.metric("Current Price", f"${buy_live_price:,.2f}" if buy_live_price else "N/A")

            buy_shares = st.number_input(
                "Shares to buy", min_value=0.0, value=1.0, step=1.0, key="buy_shares_input"
            )

            if buy_live_price and buy_shares > 0:
                st.caption(f"Estimated cost: ${buy_shares * buy_live_price:,.2f}")

            if st.button("Buy", type="primary", key="buy_button"):
                if not buy_live_price:
                    st.error("Couldn't fetch a live price for this stock. Try again in a moment.")
                else:
                    ok, msg = tradingdb.execute_buy(player_email, buy_ticker, buy_shares, buy_live_price)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with trade_tab2:

        my_holdings = tradingdb.get_holdings(player_email)

        if not my_holdings:
            st.info("You don't own any stocks yet — buy something first.")
        else:
            sell_options = [h["ticker"] for h in my_holdings]
            sell_ticker = st.selectbox("Choose a holding", sell_options, key="sell_stock_select")

            held_shares = next(
                float(h["shares"]) for h in my_holdings if h["ticker"] == sell_ticker
            )

            try:
                sell_live_price = tradingdb.fetch_current_prices([sell_ticker]).get(sell_ticker)
            except Exception:
                sell_live_price = None

            sell_col1, sell_col2 = st.columns(2)

            with sell_col1:
                st.metric("Shares Held", f"{held_shares:.4f}")

            with sell_col2:
                st.metric("Current Price", f"${sell_live_price:,.2f}" if sell_live_price else "N/A")

            sell_shares = st.number_input(
                "Shares to sell", min_value=0.0, max_value=held_shares,
                value=min(1.0, held_shares), step=1.0, key="sell_shares_input"
            )

            if sell_live_price and sell_shares > 0:
                st.caption(f"Estimated proceeds: ${sell_shares * sell_live_price:,.2f}")

            if st.button("Sell", type="primary", key="sell_button"):
                if not sell_live_price:
                    st.error("Couldn't fetch a live price for this stock. Try again in a moment.")
                else:
                    ok, msg = tradingdb.execute_sell(player_email, sell_ticker, sell_shares, sell_live_price)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with trade_tab3:

        my_holdings = tradingdb.get_holdings(player_email)

        if not my_holdings:
            st.info("No holdings yet.")
        else:
            holding_tickers = [h["ticker"] for h in my_holdings]

            try:
                current_prices = tradingdb.fetch_current_prices(holding_tickers)
            except Exception:
                current_prices = {}

            for h in my_holdings:
                ticker = h["ticker"]
                shares = float(h["shares"])
                avg_cost = float(h["avg_cost_basis"])
                price = current_prices.get(ticker, avg_cost)
                market_value = shares * price
                gain_loss_pct = ((price - avg_cost) / avg_cost * 100) if avg_cost else 0

                hcol1, hcol2, hcol3, hcol4 = st.columns([1, 1, 1, 1])

                with hcol1:
                    ticker_button(ticker, key_suffix="scenariolab_holdings", heading=True)
                    st.caption(f"{shares:.4f} shares")

                with hcol2:
                    st.write(f"Avg cost: ${avg_cost:,.2f}")
                    st.write(f"Current: ${price:,.2f}")

                with hcol3:
                    st.write(f"Value: ${market_value:,.2f}")

                with hcol4:
                    st.write(f"{gain_loss_pct:+.2f}%")

                st.divider()

    st.divider()

    # ---------------------------------------------
    # LEADERBOARD
    # ---------------------------------------------

    st.subheader("Leaderboard")

    try:
        leaderboard = tradingdb.compute_leaderboard()
    except Exception:
        leaderboard = []

    if not leaderboard:
        st.info("Leaderboard isn't available right now.")
    else:
        leaderboard_df = pd.DataFrame([
            {
                "Rank": r["rank"],
                "Trader": r["display_name"],
                "Portfolio Value": f"${r['total_value']:,.2f}",
                "Return": f"{r['return_pct']:+.2f}%",
                "Points": f"{r['total_points']:,.0f}",
                "Started": r["started_at"].strftime("%b %d, %Y"),
            }
            for r in leaderboard
        ])

        st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)

    st.divider()

    # ---------------------------------------------
    # CHALLENGES
    # ---------------------------------------------

    st.subheader("Challenges")

    try:
        active_challenges = tradingdb.get_active_challenges()
    except Exception:
        active_challenges = []

    try:
        my_participations = tradingdb.get_my_challenge_participations(player_email)
    except Exception:
        my_participations = []

    joined_challenge_ids = {p["challenge_id"] for p in my_participations}

    if not active_challenges:
        st.info("No active challenges right now — check back soon.")
    else:
        for challenge in active_challenges:
            cchcol1, cchcol2 = st.columns([3, 1])

            with cchcol1:
                st.markdown(f"**{challenge['title']}** ({challenge['period']})")
                st.caption(challenge["description"])

                reward_text = f"Reward: {float(challenge['reward_points']):.0f} points"
                if float(challenge["reward_cash"]) > 0:
                    reward_text += f" + ${float(challenge['reward_cash']):,.0f} cash"

                st.caption(reward_text)
                st.caption(f"Ends: {challenge['ends_at'].strftime('%b %d, %Y')}")

            with cchcol2:
                if challenge["id"] in joined_challenge_ids:
                    st.success("Joined")
                else:
                    if st.button("Join Challenge", key=f"join_challenge_{challenge['id']}"):
                        tradingdb.join_challenge(challenge["id"], player_email, portfolio_value)
                        st.rerun()

            st.divider()

    if my_participations:
        st.write("**Your Challenge History**")

        history_df = pd.DataFrame([
            {
                "Challenge": p["title"],
                "Started": p["joined_at"].strftime("%b %d, %Y"),
                "Money Invested": f"${float(p['starting_value']):,.2f}",
                "Return Since Start": (
                    f"{((portfolio_value - float(p['starting_value'])) / float(p['starting_value']) * 100):+.2f}%"
                    if float(p["starting_value"]) else "N/A"
                ),
                "Status": "Completed" if p["completed"] else "In Progress",
            }
            for p in my_participations
        ])

        st.dataframe(history_df, use_container_width=True, hide_index=True)

# =========================================================
# ABOUT PAGE
# =========================================================

elif page == "About":

    st.caption("ABOUT PORTFOLIOLAB")

    st.title("Making Investing Easier to Understand.")

    st.write(
        "PortfolioLab is an educational portfolio analytics "
        "tool designed to help students and first-time investors "
        "understand how different investment decisions can affect "
        "portfolio performance and risk."
    )

    st.divider()

    # -----------------------------------------------------
    # WHY I BUILT THIS
    # -----------------------------------------------------

    st.subheader("Why I Built This")

    st.write(
        "Investing can feel intimidating when you're first "
        "getting started. There are thousands of securities, "
        "different asset classes, and countless opinions about "
        "what investors should buy."
    )

    st.write(
        "I built PortfolioLab as a simple way to explore those "
        "decisions using real market data without requiring "
        "advanced financial modeling knowledge."
    )

    st.write(
        "The goal is not to tell users what to invest in. "
        "Instead, it is designed to help users understand "
        "the relationship between allocation, historical "
        "performance, diversification, and risk."
    )

    st.divider()

    # -----------------------------------------------------
    # WHAT YOU CAN DO
    # -----------------------------------------------------

    st.subheader("What You Can Explore")

    about_col1, about_col2 = st.columns(2)

    with about_col1:

        st.markdown("### Build a Portfolio")

        st.write(
            "Explore Conservative, Moderate, and Aggressive "
            "portfolio allocations using a small group of "
            "diversified ETFs."
        )

        st.markdown("### Analyze Performance")

        st.write(
            "Compare hypothetical portfolio performance "
            "with the S&P 500 over historical periods."
        )

        st.markdown("### Research ETFs")

        st.write(
            "Learn what individual ETFs are designed to "
            "provide exposure to and how they have performed "
            "historically."
        )

    with about_col2:

        st.markdown("### Understand Risk")

        st.write(
            "Explore volatility, maximum drawdown, and a "
            "simplified portfolio risk score."
        )

        st.markdown("### Run Scenarios")

        st.write(
            "Change investment amounts and risk profiles "
            "to see how hypothetical historical outcomes "
            "would have changed."
        )

        st.markdown("### Compare Decisions")

        st.write(
            "Use historical data to explore how different "
            "portfolio allocations behaved under the same "
            "market conditions."
        )

    st.divider()

    # -----------------------------------------------------
    # HOW IT WORKS
    # -----------------------------------------------------

    st.subheader("How PortfolioLab Works")

    st.write(
        "PortfolioLab follows a simple analytical process:"
    )

    step1, step2, step3, step4 = st.columns(4)

    with step1:

        st.markdown("### 01")

        st.write(
            "**Select a portfolio**"
        )

        st.caption(
            "Choose a risk profile and investment amount."
        )

    with step2:

        st.markdown("### 02")

        st.write(
            "**Pull market data**"
        )

        st.caption(
            "Historical ETF prices are retrieved through "
            "Yahoo Finance."
        )

    with step3:

        st.markdown("### 03")

        st.write(
            "**Calculate results**"
        )

        st.caption(
            "Daily returns are combined according to "
            "the portfolio's allocation."
        )

    with step4:

        st.markdown("### 04")

        st.write(
            "**Analyze the portfolio**"
        )

        st.caption(
            "Performance, risk, allocation, and scenarios "
            "are presented visually."
        )

    st.divider()

    # -----------------------------------------------------
    # METHODOLOGY
    # -----------------------------------------------------

    st.subheader("Methodology")

    methodology_col1, methodology_col2 = st.columns(2)

    with methodology_col1:

        st.markdown("### Portfolio Returns")

        st.write(
            "Daily portfolio returns are calculated by "
            "multiplying each ETF's daily return by its "
            "assigned portfolio weight and summing the results."
        )

        st.markdown("### Volatility")

        st.write(
            "Annualized volatility is estimated from the "
            "standard deviation of daily portfolio returns "
            "using 252 trading days per year."
        )

    with methodology_col2:

        st.markdown("### Maximum Drawdown")

        st.write(
            "Maximum drawdown measures the largest historical "
            "decline from a previous portfolio peak."
        )

        st.markdown("### Benchmark")

        st.write(
            "VOO is used as a simplified S&P 500 benchmark "
            "for comparing portfolio performance."
        )

    st.divider()

    # -----------------------------------------------------
    # TECHNOLOGY
    # -----------------------------------------------------

    st.subheader("Built With")

    tech1, tech2, tech3, tech4 = st.columns(4)

    with tech1:

        st.markdown("### Python")

        st.caption(
            "Core calculations and data processing"
        )

    with tech2:

        st.markdown("### Streamlit")

        st.caption(
            "Interactive web application"
        )

    with tech3:

        st.markdown("### Pandas")

        st.caption(
            "Financial data analysis"
        )

    with tech4:

        st.markdown("### yfinance")

        st.caption(
            "Historical market data"
        )

    st.divider()

    # -----------------------------------------------------
    # IMPORTANT LIMITATIONS
    # -----------------------------------------------------

    st.subheader("Important Limitations")

    st.warning(
        "PortfolioLab is an educational project and does "
        "not provide investment advice."
    )

    st.write(
        "Historical performance is not a guarantee of future "
        "results. The portfolio simulations do not account "
        "for taxes, trading costs, bid-ask spreads, dividends "
        "being paid out separately, or changes in portfolio "
        "weights over time."
    )

    st.write(
        "Risk measurements are simplified educational metrics "
        "and should not be interpreted as professional investment "
        "recommendations."
    )

    st.divider()

    # -----------------------------------------------------
    # PROJECT PHILOSOPHY
    # -----------------------------------------------------

    st.subheader("The Idea Behind PortfolioLab")

    st.markdown(
        """
        > **Don't just tell me what to invest in.  
        > Help me understand why.**
        """
    )

    st.write(
        "PortfolioLab is built around the idea that financial "
        "literacy improves when investors can experiment, "
        "compare outcomes, and understand the assumptions "
        "behind the numbers."
    )
# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "PortfolioLab · Educational portfolio analytics project"
)

st.caption(
    "Historical market data provided through Yahoo Finance "
    "via yfinance. This application does not provide "
    "personalized investment advice."
)
