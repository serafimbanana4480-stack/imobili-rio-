"""Stealth techniques for anti-bot evasion."""
import random
from typing import Dict, List
from loguru import logger


class StealthManager:
    """Advanced browser fingerprinting and stealth techniques (2026 Standard)."""

    # Real-world User-Agents updated for 2025/2026 (Chrome 134-136 range)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    ]

    # Realistic WebGL vendor/renderer combos
    WEBGL_PROFILES = [
        ("Intel Inc.", "Intel(R) Iris(TM) Plus Graphics 640"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660 Ti/PCIe/SSE2"),
        ("AMD", "AMD Radeon Pro 5500M OpenGL Engine"),
        ("Intel Inc.", "Intel(R) UHD Graphics 620"),
    ]

    def __init__(self):
        self.timezone = "Europe/Lisbon"
        self.locale = "pt-PT"
        self.webgl_vendor, self.webgl_renderer = random.choice(self.WEBGL_PROFILES)
        logger.info("StealthManager initialized with 2026 Advanced Fingerprinting")

    async def apply_stealth(self, tab):
        """Inject advanced stealth scripts into the browser tab."""
        # Random subtle canvas noise offset per session
        canvas_noise = random.randint(1, 5)
        stealth_scripts = {
            "webdriver": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});",
            "chrome_runtime": """
                if (!window.chrome) window.chrome = {};
                window.chrome.runtime = {
                    OnInstalledReason: {CHROME_UPDATE: "chrome_update", SHARED_MODULE_UPDATE: "shared_module_update", NOT_INSTALLED: "not_installed"},
                    OnRestartRequiredReason: {APP_UPDATE: "app_update", OS_UPDATE: "os_update", PERIODIC: "periodic"},
                    PlatformArch: {ARM: "arm", ARM64: "arm64", MIPS: "mips", MIPS64: "mips64", X86_32: "x86-32", X86_64: "x86-64"},
                    PlatformNaclArch: {MIPS: "mips", MIPS64: "mips64", X86_32: "x86-32", X86_64: "x86-64"},
                    PlatformOs: {ANDROID: "android", CROS: "cros", LINUX: "linux", MAC: "mac", OPENBSD: "openbsd", WIN: "win"},
                    RequestUpdateCheckStatus: {NO_UPDATE: "no_update", THROTTLED: "throttled", UPDATE_AVAILABLE: "update_available"},
                    sendMessage: function(){},
                    connect: function(){},
                    getManifest: function(){ return {manifest_version: 3}; }
                };
            """,
            "plugins": """
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: "Chrome PDF Plugin", filename: "internal-pdf-viewer", description: "Portable Document Format", version: undefined, length: 1},
                        {name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", description: "Portable Document Format", version: undefined, length: 1},
                        {name: "Native Client", filename: "internal-nacl-plugin", description: "", version: undefined, length: 2}
                    ]
                });
            """,
            "mime_types": """
                Object.defineProperty(navigator, 'mimeTypes', {
                    get: () => [
                        {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: {name: "Chrome PDF Plugin"}},
                        {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: {name: "Chrome PDF Viewer"}},
                        {type: "application/x-nacl", suffixes: "", description: "", enabledPlugin: {name: "Native Client"}}
                    ]
                });
            """,
            "languages": f"Object.defineProperty(navigator, 'languages', {{get: () => ['{self.locale}', 'pt', 'en-US', 'en']}});",
            "hardware": f"Object.defineProperty(navigator, 'hardwareConcurrency', {{get: () => {random.choice([4, 8, 12, 16])}}}); Object.defineProperty(navigator, 'deviceMemory', {{get: () => {random.choice([4, 8, 16])}}});",
            "permissions": """
                if (navigator.permissions) {
                    const origQuery = navigator.permissions.query;
                    navigator.permissions.query = function(parameters) {
                        if (parameters.name === 'notifications' || parameters.name === 'clipboard-read' || parameters.name === 'clipboard-write') {
                            return Promise.resolve({state: 'prompt', onchange: null});
                        }
                        return origQuery.apply(this, arguments);
                    };
                }
            """,
            "notification": """
                if (window.Notification) {
                    Object.defineProperty(Notification, 'permission', {get: () => 'default'});
                }
            """,
            "canvas": f"""
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                HTMLCanvasElement.prototype.toDataURL = function(type) {{
                    if (type === 'image/png') {{
                        const ctx = this.getContext('2d');
                        if (ctx) {{
                            const imgData = ctx.getImageData(0, 0, this.width, this.height);
                            for (let i = 0; i < imgData.data.length; i += 4) {{
                                imgData.data[i] = (imgData.data[i] + {canvas_noise}) % 256;
                            }}
                            ctx.putImageData(imgData, 0, 0);
                        }}
                    }}
                    return originalToDataURL.apply(this, arguments);
                }};
                CanvasRenderingContext2D.prototype.getImageData = function(sx, sy, sw, sh) {{
                    const imgData = originalGetImageData.apply(this, arguments);
                    for (let i = 0; i < imgData.data.length; i += 4) {{
                        imgData.data[i] = (imgData.data[i] + {canvas_noise}) % 256;
                    }}
                    return imgData;
                }};
            """,
            "webgl": f"""
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) return '{self.webgl_vendor}';
                    if (parameter === 37446) return '{self.webgl_renderer}';
                    if (parameter === 37447) return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
                    if (parameter === 7937) return '{self.webgl_renderer}';
                    if (parameter === 7936) return '{self.webgl_vendor}';
                    return getParameter.call(this, parameter);
                }};
                const getShaderPrecisionFormat = WebGLRenderingContext.prototype.getShaderPrecisionFormat;
                WebGLRenderingContext.prototype.getShaderPrecisionFormat = function() {{
                    return {{precision: 23, rangeMin: 127, rangeMax: 127}};
                }};
            """,
            "fonts": """
                Object.defineProperty(navigator, 'fonts', {
                    get: () => ({ check: () => Promise.resolve(true), ready: Promise.resolve({}) })
                });
            """,
            "audio": """
                const originalCreateOscillator = AudioContext.prototype.createOscillator;
                AudioContext.prototype.createOscillator = function() {
                    const oscillator = originalCreateOscillator.apply(this, arguments);
                    // Subtle frequency drift to break deterministic fingerprinting
                    const origStart = oscillator.start;
                    oscillator.start = function(when) {
                        if (oscillator.frequency && oscillator.frequency.value !== undefined) {
                            oscillator.frequency.value += 0.001;
                        }
                        return origStart.apply(this, arguments);
                    };
                    return oscillator;
                };
                // Spoof AudioBuffer copy to break audio fingerprint consistency
                const origGetChannelData = AudioBuffer.prototype.getChannelData;
                AudioBuffer.prototype.getChannelData = function(channel) {
                    const data = origGetChannelData.apply(this, arguments);
                    if (data && data.length > 0) {
                        data[data.length - 1] += 0.000001;
                    }
                    return data;
                };
            """,
            "screen": f"""
                Object.defineProperty(screen, 'colorDepth', {{get: () => 24}});
                Object.defineProperty(screen, 'pixelDepth', {{get: () => 24}});
            """,
        }

        for name, script in stealth_scripts.items():
            try:
                await tab.evaluate(script)
            except Exception as e:
                logger.warning(f"Failed to inject {name} stealth: {e}")

    def get_browser_args(self) -> List[str]:
        """Arguments for professional stealth browser start."""
        return [
            f"--user-agent={random.choice(self.USER_AGENTS)}",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            f"--lang={self.locale}",
            f"--timezone={self.timezone}",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-web-security",
            "--disable-features=BlockInsecurePrivateNetworkRequests",
            "--force-webrtc-hw-vp8-encoding",
        ]
